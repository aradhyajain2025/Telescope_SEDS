"""
Batch ground-truth test: for each target x field size, have Stellarium centre the target,
save a screenshot, solve it with ASTAP from a deliberately wrong hint, and compare with the
view centre Stellarium reports. Results go to results.csv.

Needs Stellarium open with Remote Control on, the GUI hidden (Ctrl+T) and sky clutter off.
"""
import csv
import json
import math
import random
import re
import shutil
import time
from pathlib import Path

import requests

import astap_test as t

B = "http://localhost:8090/api"
SHOTS = Path.home() / "OneDrive" / "Pictures" / "Stellarium"
OUT = Path(__file__).parent / "test_images" / "batch"
TARGETS = ["Vega", "Capella", "Betelgeuse", "Aldebaran", "Antares", "Spica", "Deneb", "Altair",
           "Arcturus", "M31", "M45", "M13", "M42", "Polaris"]
FOVS = [0.7, 1.0, 2.0, 4.0]          # image height in degrees
TOLERANCE = 0.02
HINT_OFFSET_DEG = 2.0                 # how far off the solver's starting hint is


def post(path, **data):
    requests.post(f"{B}/{path}", data=data, timeout=10).raise_for_status()


def view_center():
    v = json.loads(requests.get(f"{B}/main/view", params={"coord": "j2000"}, timeout=10).json()["j2000"])
    ra = math.degrees(math.atan2(v[1], v[0])) % 360
    dec = math.degrees(math.asin(v[2] / math.sqrt(sum(c * c for c in v))))
    return ra, dec


def screenshot():
    before = set(SHOTS.glob("stellarium-*.png"))
    post("stelaction/do", id="actionSave_Screenshot_Global")
    for _ in range(40):
        time.sleep(0.25)
        new = set(SHOTS.glob("stellarium-*.png")) - before
        if new:
            time.sleep(0.5)
            return new.pop()
    raise RuntimeError("no screenshot appeared")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(1)
    rows = []
    for name in TARGETS:
        for fov in FOVS:
            post("main/focus", target=name)
            post("main/fov", fov=fov)
            time.sleep(4)                       # let the view settle
            true_ra, true_dec = view_center()
            png = OUT / f"{re.sub('[^A-Za-z0-9]', '', name)}_fov{fov}.png"
            shutil.copy(screenshot(), png)
            ang = rng.uniform(0, 2 * math.pi)
            hint_ra = (true_ra + HINT_OFFSET_DEG * math.cos(ang) / max(0.1, math.cos(math.radians(true_dec)))) % 360
            hint_dec = max(-89, min(89, true_dec + HINT_OFFSET_DEG * math.sin(ang)))
            t0 = time.time()
            res = t.solve(png, fov, hint_ra / 15, hint_dec, radius=8, tolerance=TOLERANCE)
            secs = time.time() - t0
            err = t.sep_arcsec(res["ra_deg"], res["dec_deg"], true_ra, true_dec) if res else None
            rows.append({"target": name, "fov_deg": fov, "solved": bool(res),
                         "error_arcsec": None if err is None else round(err, 1),
                         "scale_arcsec_px": None if not res else round(res["scale_arcsec_px"], 3),
                         "solve_seconds": round(secs, 1)})
            print(rows[-1], flush=True)
    with open(Path(__file__).parent / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    ok = [r for r in rows if r["solved"]]
    print(f"\nsolved {len(ok)}/{len(rows)}")
    for fov in FOVS:
        sub = [r for r in rows if r["fov_deg"] == fov]
        good = sorted(r["error_arcsec"] for r in sub if r["solved"])
        med = good[len(good) // 2] if good else None
        print(f"  fov {fov}: {len(good)}/{len(sub)} solved, median error {med} arcsec")


if __name__ == "__main__":
    main()
