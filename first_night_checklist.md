# First Real Night Checklist

Written before the hardware exists; adjust after the first bench test. I did not create a N.I.N.A. sequence file - its format is version-specific and untestable without the app. Build the sequence in N.I.N.A.'s Sequencer (Slew & Center, Start Tracking, Take Exposure) and save it.

## Before dark (bench)
- [ ] Firmware compiled (Arduino IDE, ESP32 Dev Module) with `config_calculator.py --apply` using the *real* drive ratio
- [ ] Drivers' Vref / current set; motor turns, direction correct (else `AXIS1_DRIVER_REVERSE`)
- [ ] Connect through the OnStep ASCOM driver; `:GVP#` answers
- [ ] 1 full platform revolution test: marked rotation matches steps/degree
- [ ] Platform polar-aligned (latitude angle set; see Poncet platform docs)
- [ ] ASTAP + D80 installed, path set in N.I.N.A.; camera connects

## At the telescope
1. Power mount; confirm tracking starts (TRACK_AUTOSTART).
2. N.I.N.A.: connect camera and OnStep telescope; set site latitude/longitude and time (laptop clock correct!).
3. Slew to a bright star, take a 2-5 s exposure, **Plate Solve**; if it fails raise the exposure or check the focus.
4. **Sync** the mount to the solved position.
5. Sky Atlas -> target -> **Slew and Center**; confirm "centering successful".
6. Expose 60 s frames; check star trails. If trailing: check polar alignment, then drive ratio (`AXIS1_STEPS_PER_DEGREE` error shows as steady drift).

## Record
Drift in arcsec over 10 min, compared with the simulator's ~20" baseline.
