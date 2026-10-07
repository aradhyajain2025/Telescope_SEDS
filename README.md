# Telescope Automation

A Dobsonian on a Poncet (equatorial) platform, driven by an ESP32 running OnStep and controlled from a laptop through ASCOM, N.I.N.A. and ASTAP plate solving.

## Where things are
- `project_explainer.md` - design and rationale
- `implementation_plan.md` - current status and remaining work
- `laptop_software_setup.md` / `laptop_software_setup/` - install order and installers
- `walkthrough.md`, `test_plan.md` - zero-hardware simulator demo and validation tests
- `OnStep_Config_Template/config_calculator.py` - computes steps/degree and writes a valid OnStep `Config.h`
- `OnStep_Config_Template/AstroResorces(Shared)/` - OnStep 4.24s source and mechanical resources
- `archive/` - the superseded Python/OpenCV/Stellarium prototype

## Generate the firmware config
```bash
python OnStep_Config_Template/config_calculator.py --pulley 16 --gear 400 --apply
```
`--pulley` and `--gear` are placeholders until the drive train is final (`--extra-reduction` adds e.g. a harmonic drive stage). Then open `OnStep.ino` in the Arduino IDE (board: ESP32 Dev Module) and press Verify.
