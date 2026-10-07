"""LX200/OnStep client over TCP. The same code works against the simulator and a
real OnStep WiFi controller (default 192.168.0.1:9999)."""
import socket
import time

from onstep_sim import fmt_dec, fmt_ra, parse_dec, parse_ra


class OnStepClient:
    def __init__(self, host="127.0.0.1", port=9999, timeout=3.0):
        self.s = socket.create_connection((host, port), timeout=timeout)

    def _cmd(self, cmd, reply="#"):
        self.s.sendall(f":{cmd}#".encode())
        if reply is None:
            return None
        if reply == "1":  # single-char reply
            return self.s.recv(1).decode()
        buf = b""
        while not buf.endswith(b"#"):
            buf += self.s.recv(64)
        return buf.decode().rstrip("#")

    def version(self):
        return self._cmd("GVP") + " " + self._cmd("GVN")

    def position(self):
        return parse_ra(self._cmd("GR")), parse_dec(self._cmd("GD"))

    def _set_target(self, ra, dec):
        if self._cmd(f"Sr{fmt_ra(ra)}", "1") != "1" or self._cmd(f"Sd{fmt_dec(dec)}", "1") != "1":
            raise RuntimeError("mount rejected target")

    def goto(self, ra, dec, wait=True):
        self._set_target(ra, dec)
        if self._cmd("MS", "1") != "0":
            raise RuntimeError("goto refused")
        while wait and self.is_slewing():
            time.sleep(0.05)

    def sync(self, ra, dec):
        self._set_target(ra, dec)
        self._cmd("CM")

    def is_slewing(self):
        return "\x7f" in self._cmd("D")

    def set_tracking(self, on):
        self._cmd("Te" if on else "Td", "1")

    def abort(self):
        self._cmd("Q", None)
