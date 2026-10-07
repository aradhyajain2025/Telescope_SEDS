# Driving N.I.N.A. from the simulated OnStep

Goal: N.I.N.A. + ASTAP run the real closed loop against the simulated mount. **Untested** - the serial path is checked only with a fake stream (`simulation/test_serial.py`); I could not run N.I.N.A. or com0com here.

## One-time setup
1. Install **com0com** (virtual COM port pair, needs admin; use the signed build). Create a pair, e.g. `COM5 <-> COM6`.
2. `pip install numpy pyserial`

## Each session
```bash
cd simulation
python onstep_sim.py --serial COM5 --time-scale 20
```
In N.I.N.A.: Equipment > Telescope > **OnStep Telescope** > gear icon > port **COM6**, 9600 baud > Connect.

If the OnStep ASCOM driver's setup window has a network/IP option, use `127.0.0.1` port `9999` instead and skip com0com.

## What to expect / likely problems
- The simulator implements only: `:GR :GD :Sr :Sd :MS :CM :Q :D :Te :Td :GVP :GVN`. The ASCOM driver may send others (`:GU#` status, `:Gt/:Gg` site, `:GS` sidereal time, `:Gr/:Gd`, park/home). Unknown commands currently get `0`. If the driver refuses to connect, run the simulator, note which command it stalls on (add a `print(cmd)` in `Handler.execute`) and add a reply - usually a one-line change.
- **Camera**: N.I.N.A.'s Camera Simulator can show the sky for the *telescope simulator's* position, not ours. For the plate-solve step either (a) use the N.I.N.A. Telescope Simulator + Camera Simulator (walkthrough.md), or (b) accept that with our mount the images are from N.I.N.A.'s sim and won't match. The fully consistent version is `simulation/demo.py`.
- ASTAP needs the D80 database installed and its path set in N.I.N.A. Options > Plate Solving.
