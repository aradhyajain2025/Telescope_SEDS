"""
Re-try the batch images that ASTAP failed on (or solved at the wrong scale) with progressively
more permissive settings, to see which setting rescues which image. Uses the existing images.
Truth is the object's J2000 position from Stellarium; the hint is 2 deg off, as in batch.py.
"""
import math
import random
import re
from pathlib import Path

import astap_test as t

BATCH = Path(__file__).parent / "test_images" / "batch"
NAMES = {"Vega": "Vega", "Capella": "Capella", "Betelgeuse": "Betelgeuse", "Aldebaran": "Aldebaran",
         "Antares": "Antares", "Spica": "Spica", "Deneb": "Deneb", "Altair": "Altair",
         "Arcturus": "Arcturus", "M31": "M31", "M45": "M45", "M13": "M13", "M42": "M42",
         "Polaris": "Polaris"}
CONFIGS = [
    ("baseline  -t .02 -r 8",            dict(tolerance=0.02, radius=8, extra=())),
    ("more stars -s 300",                dict(tolerance=0.02, radius=8, extra=("-s", "300"))),
    ("looser    -t .03 -s 300",          dict(tolerance=0.03, radius=8, extra=("-s", "300"))),
    ("wider     -r 15 -t .03 -s 300",    dict(tolerance=0.03, radius=15, extra=("-s", "300"))),
    ("slow      -r 15 -t .03 -s 300",    dict(tolerance=0.03, radius=15, extra=("-s", "300", "-speed", "slow"))),
    ("min star  -m 5 -t .03 -s 300",     dict(tolerance=0.03, radius=15, extra=("-s", "300", "-m", "5"))),
]


def main():
    rng = random.Random(5)
    summary = {c[0]: 0 for c in CONFIGS}
    images = sorted(BATCH.glob("*.png"))
    for png in images:
        m = re.match(r"([A-Za-z0-9]+)_fov([\d.]+)\.png", png.name)
        target, fov = m.group(1), float(m.group(2))
        ra_h, dec = t.stellarium_truth(NAMES[target])
        ang = rng.uniform(0, 2 * math.pi)
        hint_ra = (ra_h * 15 + 2 * math.cos(ang) / max(0.1, math.cos(math.radians(dec)))) % 360 / 15
        hint_dec = max(-89, min(89, dec + 2 * math.sin(ang)))
        line = f"{png.stem:22s}"
        first = None
        for label, kw in CONFIGS:
            r = t.solve(png, fov, hint_ra, hint_dec, **kw)
            good = bool(r and r["scale_ok"] and t.sep_arcsec(r["ra_deg"], r["dec_deg"], ra_h * 15, dec) < 120)
            line += " Y" if good else (" w" if r else " .")
            if good:
                summary[label] += 1
                first = first or label
        print(line, "->", first or "NEVER SOLVED", flush=True)
    print("\nsolved correctly (Y), wrong/false solution (w), no solution (.)")
    for label, n in summary.items():
        print(f"  {label}: {n}/{len(images)}")


if __name__ == "__main__":
    main()
