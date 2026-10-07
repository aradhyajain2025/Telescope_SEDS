"""
Proof-of-concept: closed-loop GoTo + tracking with no hardware.

  simulated OnStep (LX200 over TCP)  <-- onstep_client -->  this script (the N.I.N.A. role)
  simulated camera frame --> plate solver --> sync + re-slew until centred

Run:  python demo.py
"""
import math
import os
import time

import onstep_sim
import skysim
from onstep_client import OnStepClient

TARGET_NAME, TARGET = "M42 (Orion Nebula)", (83.8221, -5.3911)   # RA, Dec in degrees
TOLERANCE_ARCSEC = 30.0
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def sep_arcsec(a, b):
    dra = ((a[0] - b[0] + 180) % 360 - 180) * math.cos(math.radians(a[1]))
    return math.hypot(dra, a[1] - b[1]) * 3600


def expose_and_solve(cat, mount, name):
    """Take a frame at the mount's TRUE pointing, solve it near the REPORTED pointing."""
    truth = mount.truth()
    img = skysim.render(cat, *truth, seed=int(time.time() * 1000) % 2**31)
    skysim.save_png(img, os.path.join(OUT, name))
    return truth, skysim.solve(img, *mount.reported(), cat=cat)


def main():
    os.makedirs(OUT, exist_ok=True)
    print("Building synthetic sky catalog...")
    cat = skysim.Catalog()
    srv = onstep_sim.start(time_scale=20.0, seed=7)
    mount = srv.mount
    client = OnStepClient()
    print("Connected to:", client.version())
    client.set_tracking(True)      # firmware does this itself with TRACK_AUTOSTART ON
    print(f"Mount starts misaligned: reports {mount.reported()} but truly at {mount.truth()}\n")

    print(f"=== Slew and Center: {TARGET_NAME} ===")
    for attempt in range(1, 6):
        client.goto(*TARGET)
        truth, res = expose_and_solve(cat, mount, f"frame_{attempt}.png")
        if res is None:
            print(f"  [{attempt}] plate solve FAILED")
            continue
        solved = res[:2]
        err = sep_arcsec(solved, TARGET)
        print(f"  [{attempt}] solved RA {solved[0]:.4f} Dec {solved[1]:.4f} ({res[2]} matches) "
              f"| error {err:.0f} arcsec (ground truth {sep_arcsec(truth, TARGET):.0f})")
        if err <= TOLERANCE_ARCSEC:
            print("  Centering successful.\n")
            break
        client.sync(*solved)          # tell OnStep where it REALLY is, then re-slew
    else:
        print("  FAILED to center\n")
        return

    print("=== Tracking test: 10 simulated minutes ===")
    for label, on in (("tracking ON ", True), ("tracking OFF", False)):
        client.goto(*TARGET)
        _, r0 = expose_and_solve(cat, mount, "t0.png")
        client.set_tracking(on)
        time.sleep(600 / mount.time_scale)
        _, r1 = expose_and_solve(cat, mount, f"t10_{'on' if on else 'off'}.png")
        client.set_tracking(True)
        drift = sep_arcsec(r0[:2], r1[:2]) if r0 and r1 else float("nan")
        print(f"  {label}: image drifted {drift:7.0f} arcsec in 10 min")
    print(f"\nFrames saved to {OUT}")
    srv.shutdown()


if __name__ == "__main__":
    main()
