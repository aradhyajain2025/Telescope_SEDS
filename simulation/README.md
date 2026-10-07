# Software proof of concept (no hardware)

```bash
pip install numpy
python demo.py        # ~10 s, writes frames to output/
```

| File | Role | Real-system equivalent |
|------|------|------------------------|
| `onstep_sim.py` | Fake OnStep mount, LX200 over TCP port 9999. Mount starts misaligned; gotos have error; sync fixes the offset | ESP32 running OnStep |
| `onstep_client.py` | goto / sync / track / position commands | OnStep ASCOM driver |
| `skysim.py` | Synthetic star catalog, camera frame renderer, simple plate solver | Camera + ASTAP |
| `demo.py` | Slew -> expose -> solve -> sync -> re-slew until within 30", then a tracking drift test | N.I.N.A. "Slew and Center" |

Typical result: first slew misses by ~3.7 degrees (misalignment), second lands within ~20 arcsec; 10 min with tracking drifts ~20", without tracking ~2.5 degrees.

Limits: the sky is random, not real; the solver assumes known scale/orientation (ASTAP solves those too); the mount model is a simple pointing-error model, not the real motor/gear dynamics.

To use against the real mount later, point `OnStepClient(host, port)` at the OnStep controller (WiFi default 192.168.0.1:9999). To drive N.I.N.A. from the simulator, the OnStep ASCOM driver needs a serial port, which would need a TCP-to-virtual-COM bridge (e.g. com0com + a forwarder); not done yet.
