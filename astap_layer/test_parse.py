"""Checks the .ini parser and error maths with a hand-made file (no ASTAP or image needed)."""
import tempfile
from pathlib import Path

import astap_test as t

ini = "PLTSOLVD=T\nCRVAL1=83.8221\nCRVAL2=-5.3911\nCDELT1=-0.0021\nCDELT2=0.0021\nCROTA2=1.5\n"
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "x.ini"
    p.write_text(ini)
    r = t.parse_ini(p)
assert r["PLTSOLVD"] == "T" and float(r["CRVAL1"]) == 83.8221
assert abs(t.sep_arcsec(10, 0, 10 + 1 / 3600, 0) - 1.0) < 1e-6
assert abs(t.sep_arcsec(359.9999, 0, 0.0001, 0) - 0.72) < 0.01     # RA wrap-around
print("parser and error maths OK")
