"""
OnStep Config calculator for a Poncet (equatorial) platform.

Computes AXIS1_STEPS_PER_DEGREE from the drive train and writes a Config.h by
patching the stock OnStep 4.24s Config.h that ships in
AstroResorces(Shared)/OnStep. Patching the real file (instead of generating one
from scratch) keeps every option the firmware's Validate.h expects, so the sketch
compiles.

Usage:
    python config_calculator.py                       # defaults below, writes ./Config.h
    python config_calculator.py --pulley 16 --gear 400 --apply

--apply also copies the result over OnStep/Config.h (the old one is kept as Config.h.bak).
"""
import argparse
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ONSTEP_DIR = HERE / "AstroResorces(Shared)" / "OnStep"
STOCK_CONFIG = ONSTEP_DIR / "Config.h"


def steps_per_degree(step_angle, microsteps, pulley_teeth, gear_teeth):
    ratio = gear_teeth / pulley_teeth
    return (360.0 / step_angle) * microsteps * ratio / 360.0, ratio


def read(path):
    # newline="" keeps the stock file's line endings so diffs stay minimal
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return f.read()


def patch(text, name, value):
    """Replace the value of `#define NAME value //comment`, keeping the comment."""
    pattern = re.compile(rf"^(#define\s+{name}\s+)(\"[^\"]*\"|\S+)(?=\s*//|\s*$)", re.M)
    new, n = pattern.subn(lambda m: f"{m.group(1)}{value}", text, count=1)
    if n != 1:
        raise SystemExit(f"Config.h has no '#define {name}' - wrong OnStep version?")
    return new


def build_config(spd, microsteps):
    text = read(STOCK_CONFIG)
    if not (STOCK_CONFIG.with_suffix(".h.stock")).exists():
        shutil.copy(STOCK_CONFIG, STOCK_CONFIG.with_suffix(".h.stock"))
    else:
        text = read(STOCK_CONFIG.with_suffix(".h.stock"))

    settings = {
        # WeMos D1 R32 (ESP32) + CNC V3 shield = the "MaxESP CnC v3" pinmap
        "PINMAP": "CNC3",
        # A Poncet platform tracks like a GEM's RA axis; Axis2 is unused
        "MOUNT_TYPE": "GEM",
        "TRACK_AUTOSTART": "ON",
        "SLEW_RATE_BASE_DESIRED": "1.0",
        # AXIS1 (platform drive)
        "AXIS1_STEPS_PER_DEGREE": f"{spd:.5f}",
        "AXIS1_STEPS_PER_WORMROT": "0",  # no worm -> PEC disabled
        "AXIS1_DRIVER_MODEL": "TMC2209_QUIET",  # stealthChop tracking, spreadCycle slews
        "AXIS1_DRIVER_MICROSTEPS": str(microsteps),
        "AXIS1_DRIVER_MICROSTEPS_GOTO": "OFF",
        # AXIS2 is not wired on a single-axis platform, but keep it valid
        "AXIS2_STEPS_PER_DEGREE": f"{spd:.5f}",
        "AXIS2_DRIVER_MODEL": "TMC2209_QUIET",
        "AXIS2_DRIVER_MICROSTEPS": str(microsteps),
        "ST4_INTERFACE": "OFF",  # guiding goes over ASCOM
    }
    for name, value in settings.items():
        text = patch(text, name, value)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step-angle", type=float, default=1.8, help="motor degrees/full step (default 1.8)")
    ap.add_argument("--microsteps", type=int, default=64, choices=[8, 16, 32, 64], help="TMC2209 standalone modes")
    ap.add_argument("--pulley", type=float, default=16, help="motor pulley teeth (default 16 - PLACEHOLDER)")
    ap.add_argument("--gear", type=float, default=400, help="driven gear teeth (default 400 - PLACEHOLDER)")
    ap.add_argument("--extra-reduction", type=float, default=1.0,
                    help="additional reduction, e.g. 100 for a 100:1 harmonic drive (default 1)")
    ap.add_argument("--out", default=str(HERE / "Config.h"))
    ap.add_argument("--apply", action="store_true", help="also install into OnStep/Config.h")
    a = ap.parse_args()

    spd, ratio = steps_per_degree(a.step_angle, a.microsteps, a.pulley, a.gear)
    spd *= a.extra_reduction
    ratio *= a.extra_reduction
    print(f"step angle {a.step_angle} deg, {a.microsteps} microsteps, total reduction {ratio:g}:1")
    print(f"AXIS1_STEPS_PER_DEGREE = {spd:.5f}")

    with open(a.out, "w", encoding="utf-8", newline="") as f:
        f.write(build_config(spd, a.microsteps))
    print(f"wrote {a.out}")
    if a.apply:
        target = ONSTEP_DIR / "Config.h"
        shutil.copy(target, target.with_suffix(".h.bak"))
        shutil.copy(a.out, target)
        print(f"installed into {target}")


if __name__ == "__main__":
    main()
