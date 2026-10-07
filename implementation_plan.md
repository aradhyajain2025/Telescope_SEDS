# Implementation Plan

## State after review
- **Software stack** (ASCOM, OnStep driver, N.I.N.A., ASTAP + D80): installers are in `laptop_software_setup/`; docs describe the install order. Simulator demo steps are in `walkthrough.md` / `test_plan.md`.
- **Firmware config**: the old `Config.h` used options that don't exist in OnStep 4.24s (`MOUNT_TYPE "Equatorial"`, quoted `PINMAP`, `AXIS1_MICROSTEPS`, ...), so it would not compile. **Fixed**: `config_calculator.py` now patches the stock OnStep `Config.h` (CNC3 pinmap, GEM, TMC2209_QUIET, 64 microsteps, PEC off) and `--apply` installs it.
- **Archive** (Stellarium/OpenCV scripts): superseded, leave as is. `README.md` still describes them; it is stale.

## Done: software simulation PoC (`simulation/`)
Fake OnStep (LX200/TCP) + synthetic camera + solver + closed-loop demo. See `simulation/README.md`.

## Also written
- `simulation/onstep_sim.py --serial COMx` (serial front-end, unit-tested with a fake stream only)
- `nina_with_simulator.md`, `hardware_interface_spec.md`, `first_night_checklist.md`

## Remaining work
| # | Task | Blocked on |
|---|------|-----------|
| 1 | Compile `OnStep.ino` for ESP32 Dev Module with the new Config.h (Test 1) | Arduino IDE + ESP32 core installed |
| 2 | Set the real drive ratio: `python config_calculator.py --pulley N --gear N [--extra-reduction N] --apply`. Current 16:400 is a placeholder | Final mechanical design (Poncet belt/gear vs. harmonic drive) |
| 3 | Run N.I.N.A. simulator demo (Tests 2-3), confirm ASTAP solves; then try `nina_with_simulator.md` | You, at the laptop (GUI) |
| 4 | Flash ESP32, connect through the OnStep ASCOM driver, verify direction (`AXIS1_DRIVER_REVERSE`) and sidereal rate | Hardware |
| 5 | Set driver current (Vref on TMC2209 boards) and platform travel limits (`AXIS1_LIMIT_MIN/MAX`) | Hardware |

## Open questions for you
- Final drive train: belt/pulley numbers, or the harmonic drive in `resources/`?
- Is a second axis (Dec) planned? Config assumes RA only.
