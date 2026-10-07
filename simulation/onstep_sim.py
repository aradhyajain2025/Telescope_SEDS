"""
Simulated OnStep mount: a TCP server speaking the LX200 subset OnStep uses
(OnStep over WiFi listens on port 9999). Anything that talks to a real OnStep
(onstep_client.py, and later the OnStep ASCOM driver / N.I.N.A.) can talk to this.

The mount keeps a TRUE pointing (where the tube really looks) and a REPORTED
pointing (what OnStep believes). reported = true + sync offset. Gotos land with
a small random error, and a sync (:CM#) changes only the offset. That is
exactly why plate solving + sync is needed in the real system.
"""
import random
import socketserver
import threading
import time

SIDEREAL_DEG_PER_S = 360.0 / 86164.0905  # RA drift of an untracked scope


def wrap360(a):
    return a % 360.0


def fmt_ra(deg):
    s = round(wrap360(deg) / 15.0 * 3600) % 86400
    return f"{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}"


def fmt_dec(deg):
    sign = "+" if deg >= 0 else "-"
    s = round(abs(deg) * 3600)
    return f"{sign}{s // 3600:02d}*{s // 60 % 60:02d}:{s % 60:02d}"


def parse_ra(txt):
    h, m, s = (float(x) for x in txt.split(":"))
    return (h + m / 60 + s / 3600) * 15.0


def parse_dec(txt):
    sign = -1 if txt.startswith("-") else 1
    d, rest = txt.lstrip("+-").split("*")
    m, s = (float(x) for x in rest.split(":"))
    return sign * (float(d) + m / 60 + s / 3600)


class MountModel:
    def __init__(self, time_scale=1.0, slew_rate=4.0, seed=None,
                 initial_offset=(3.0, -2.0), tracking_error_arcsec_min=2.0):
        self.lock = threading.RLock()
        self.rng = random.Random(seed)
        self.time_scale = time_scale
        self.slew_rate = slew_rate              # deg/s (simulated time)
        self.true_ra, self.true_dec = 0.0, 0.0
        self.off_ra, self.off_dec = initial_offset  # mount starts badly aligned
        self.tracking = False
        self.slewing = False
        self.goal = None
        self.target_ra = self.target_dec = 0.0
        self.track_err = tracking_error_arcsec_min / 3600.0 / 60.0  # deg/s
        self._stop = False
        self._last = time.monotonic()
        threading.Thread(target=self._run, daemon=True).start()

    # --- state ---
    def reported(self):
        with self.lock:
            return wrap360(self.true_ra + self.off_ra), max(-90, min(90, self.true_dec + self.off_dec))

    def truth(self):
        with self.lock:
            return wrap360(self.true_ra), self.true_dec

    # --- commands ---
    def goto(self):
        with self.lock:
            dec_t = self.target_dec - self.off_dec
            ra_t = self.target_ra - self.off_ra
            dist = max(abs(((ra_t - self.true_ra + 180) % 360) - 180), abs(dec_t - self.true_dec))
            sigma = 0.0005 + 0.003 * dist  # deg: pointing error grows with slew length
            self.goal = (ra_t + self.rng.gauss(0, sigma), dec_t + self.rng.gauss(0, sigma))
            self.slewing = True

    def sync(self):
        with self.lock:
            self.off_ra = self.target_ra - self.true_ra
            self.off_dec = self.target_dec - self.true_dec

    def abort(self):
        with self.lock:
            self.slewing = False
            self.goal = None

    # --- physics ---
    def _run(self):
        while not self._stop:
            now = time.monotonic()
            dt = (now - self._last) * self.time_scale
            self._last = now
            with self.lock:
                if self.slewing and self.goal:
                    step = self.slew_rate * dt
                    gra, gdec = self.goal
                    dra = ((gra - self.true_ra + 180) % 360) - 180
                    ddec = gdec - self.true_dec
                    if max(abs(dra), abs(ddec)) <= step:
                        self.true_ra, self.true_dec = wrap360(gra), gdec
                        self.slewing = False
                    else:
                        k = step / max(abs(dra), abs(ddec))
                        self.true_ra = wrap360(self.true_ra + dra * k)
                        self.true_dec += ddec * k
                elif not self.tracking:
                    self.true_ra = wrap360(self.true_ra + SIDEREAL_DEG_PER_S * dt)
                else:
                    self.true_ra = wrap360(self.true_ra + self.track_err * dt)
            time.sleep(0.01)

    def close(self):
        self._stop = True


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        m = self.server.mount
        buf = ""
        while True:
            data = self.request.recv(1024)
            if not data:
                return
            buf += data.decode("ascii", "ignore")
            while ":" in buf and "#" in buf[buf.index(":"):]:
                start = buf.index(":")
                end = buf.index("#", start)
                cmd, buf = buf[start + 1:end], buf[end + 1:]
                reply = self.execute(m, cmd)
                if reply is not None:
                    self.request.sendall(reply.encode("ascii"))

    @staticmethod
    def execute(m, cmd):
        if cmd == "GR":
            return fmt_ra(m.reported()[0]) + "#"
        if cmd == "GD":
            return fmt_dec(m.reported()[1]) + "#"
        if cmd.startswith("Sr"):
            m.target_ra = parse_ra(cmd[2:].strip())
            return "1"
        if cmd.startswith("Sd"):
            m.target_dec = parse_dec(cmd[2:].strip())
            return "1"
        if cmd == "MS":
            m.goto()
            return "0"
        if cmd == "CM":
            m.sync()
            return "N/A#"
        if cmd == "Q":
            m.abort()
            return None
        if cmd == "D":
            return "\x7f#" if m.slewing else "#"
        if cmd == "Te":
            m.tracking = True
            return "1"
        if cmd == "Td":
            m.tracking = False
            return "1"
        if cmd == "GVP":
            return "On-Step#"
        if cmd == "GVN":
            return "4.24s (sim)#"
        return "0"


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start(port=9999, **kw):
    srv = Server(("127.0.0.1", port), Handler)
    srv.mount = MountModel(**kw)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def serve_serial(port, mount, baud=9600, stream=None):
    """Serve the same LX200 commands on a serial port (e.g. one end of a com0com
    virtual pair) so the OnStep ASCOM driver / N.I.N.A. can connect to the simulator.
    `stream` can be any object with read(n)/write(bytes) - used by the tests."""
    if stream is None:
        import serial
        stream = serial.Serial(port, baud, timeout=0.2)
    buf = ""
    while True:
        data = stream.read(256)
        if data is None:
            return
        buf += data.decode("ascii", "ignore")
        while ":" in buf and "#" in buf[buf.index(":"):]:
            start = buf.index(":")
            end = buf.index("#", start)
            cmd, buf = buf[start + 1:end], buf[end + 1:]
            reply = Handler.execute(mount, cmd)
            if reply is not None:
                stream.write(reply.encode("ascii"))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Simulated OnStep mount")
    ap.add_argument("--serial", metavar="COMx", help="also serve on this COM port (one end of a virtual pair)")
    ap.add_argument("--time-scale", type=float, default=1.0, help="1 = real time")
    a = ap.parse_args()
    s = start(time_scale=a.time_scale)
    print("Simulated OnStep listening on tcp 127.0.0.1:9999 (Ctrl+C to stop)")
    try:
        if a.serial:
            print(f"and serial {a.serial}")
            serve_serial(a.serial, s.mount)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
