"""
Solve an image with the ASTAP command line and compare with the known true position.
Only the confirmed test tooling (tasks 2-3): no closed-loop logic here.

  python astap_test.py frame.png --fov 1.5 --ra 5.588 --dec -5.39            # truth given by hand
  python astap_test.py frame.png --fov 1.5 --ra 5.588 --dec -5.39 --stellarium M42   # truth from Stellarium

--ra is in HOURS, --dec in degrees (J2000). They are used both as the solver hint and,
unless --stellarium is given, as the truth. --fov is the field DIAMETER/height in degrees
as ASTAP's -fov expects (check `astap_cli -h` for your version).
"""
import argparse
import math
import struct
import subprocess
from pathlib import Path

ASTAP = r"C:\Program Files\astap\astap_cli.exe"


def parse_ini(path):
    """ASTAP writes KEY=VALUE lines (PLTSOLVD, CRVAL1/2 in degrees, CDELT1/2 deg/px, CROTA2...)."""
    d = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def png_size(path):
    """(width, height) of a PNG, or None for other formats."""
    with open(path, "rb") as f:
        head = f.read(24)
    if head[1:4] != b"PNG":
        return None
    return struct.unpack(">II", head[16:24])


def solve(image, fov, ra_hours, dec_deg, radius=10.0, tolerance=0.007, astap=ASTAP, extra=(), scale_tol=0.1):
    """Run ASTAP; return dict with ra_deg, dec_deg, scale_arcsec_px, rotation_deg or None."""
    cmd = [astap, "-f", str(image), "-fov", str(fov), "-ra", str(ra_hours),
           "-spd", str(dec_deg + 90.0), "-r", str(radius), "-t", str(tolerance), "-wcs", "-log", *extra]
    subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    ini = Path(image).with_suffix(".ini")
    if not ini.exists():
        return None
    d = parse_ini(ini)
    if d.get("PLTSOLVD", "F").upper() != "T":
        return None
    scale = abs(float(d["CDELT2"])) * 3600
    size = png_size(image)
    expected = fov * 3600 / size[1] if size else None
    # ASTAP can report a "solution" at the wrong scale; reject it if far from what -fov implies
    scale_ok = expected is None or abs(scale / expected - 1) <= scale_tol
    return {"ra_deg": float(d["CRVAL1"]), "dec_deg": float(d["CRVAL2"]),
            "scale_arcsec_px": scale, "expected_scale": expected, "scale_ok": scale_ok,
            "rotation_deg": float(d.get("CROTA2", 0))}


def stellarium_truth(name, host="localhost", port=8090):
    """True J2000 position of a named object from Stellarium's Remote Control API."""
    import requests
    base = f"http://{host}:{port}/api"
    requests.post(f"{base}/main/focus", data={"target": name}, timeout=5).raise_for_status()
    info = requests.get(f"{base}/objects/info", params={"format": "json"}, timeout=5).json()
    # raJ2000/decJ2000 are in degrees; plain "ra"/"dec" are of-date and would not match ASTAP
    return (info["raJ2000"] % 360) / 15.0, info["decJ2000"]   # Stellarium can return negative RA


def sep_arcsec(ra1_deg, dec1, ra2_deg, dec2):
    dra = ((ra1_deg - ra2_deg + 180) % 360 - 180) * math.cos(math.radians((dec1 + dec2) / 2))
    return math.hypot(dra, dec1 - dec2) * 3600


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--fov", type=float, required=True)
    ap.add_argument("--ra", type=float, required=True, help="hours")
    ap.add_argument("--dec", type=float, required=True, help="degrees")
    ap.add_argument("--radius", type=float, default=10.0)
    ap.add_argument("--tolerance", type=float, default=0.007,
                    help="ASTAP quad tolerance; Stellarium screenshots need ~0.02 (default 0.007 fails)")
    ap.add_argument("--stellarium", metavar="NAME", help="take truth from Stellarium for this object")
    a = ap.parse_args()

    t_ra, t_dec = (stellarium_truth(a.stellarium) if a.stellarium else (a.ra, a.dec))
    res = solve(a.image, a.fov, a.ra, a.dec, a.radius, a.tolerance)
    if res is None:
        print("ASTAP did not solve the image (see the .log next to it)")
        raise SystemExit(1)
    if not res["scale_ok"]:
        print(f"REJECTED: solved scale {res['scale_arcsec_px']:.2f} arcsec/px but --fov implies "
              f"{res['expected_scale']:.2f}; this is a false solution")
        raise SystemExit(2)
    err = sep_arcsec(res["ra_deg"], res["dec_deg"], t_ra * 15, t_dec)
    print(f"solved: RA {res['ra_deg'] / 15:.5f} h, Dec {res['dec_deg']:+.5f} deg, "
          f"scale {res['scale_arcsec_px']:.2f} arcsec/px, rotation {res['rotation_deg']:.1f} deg")
    print(f"truth : RA {t_ra:.5f} h, Dec {t_dec:+.5f} deg")
    print(f"error : {err:.1f} arcsec")


if __name__ == "__main__":
    main()
