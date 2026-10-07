"""
Synthetic sky: star catalog, camera frame renderer, and a plate solver standing in
for ASTAP. The catalog is random (seeded) - it is NOT the real sky, but it is a
fixed sky that both the camera and the solver share, which is all the closed loop
needs. Swap in real ASTAP + a real camera later.
"""
import struct
import zlib

import numpy as np

W, H = 1280, 960
SCALE_ARCSEC = 7.0                      # arcsec / pixel -> ~2.5 x 1.9 deg field
SCALE_DEG = SCALE_ARCSEC / 3600.0
PSF_SIGMA = 1.6
MAG_LIMIT = 11.6                        # faintest star the camera/solver use


class Catalog:
    def __init__(self, n=1_000_000, seed=42):
        rng = np.random.default_rng(seed)
        ra = rng.uniform(0, 360, n)
        dec = np.degrees(np.arcsin(rng.uniform(-1, 1, n)))
        u = rng.uniform(0, 1, n)
        mag = 6 + 2 * np.log10(1 + u * (10 ** 3.5 - 1))
        keep = mag < MAG_LIMIT
        self.ra, self.dec, self.mag = ra[keep], dec[keep], mag[keep]

    def cone(self, ra0, dec0, radius):
        d = np.abs(self.dec - dec0) < radius
        ra, dec, mag = self.ra[d], self.dec[d], self.mag[d]
        dra = (ra - ra0 + 180) % 360 - 180
        k = np.abs(dra) * np.cos(np.radians(dec0)) < radius * 1.5
        return ra[k], dec[k], mag[k]


def to_tangent(ra, dec, ra0, dec0):
    """Gnomonic projection -> (xi east, eta north) in degrees."""
    ra, dec, ra0, dec0 = map(np.radians, (ra, dec, ra0, dec0))
    cosc = np.sin(dec0) * np.sin(dec) + np.cos(dec0) * np.cos(dec) * np.cos(ra - ra0)
    xi = np.cos(dec) * np.sin(ra - ra0) / cosc
    eta = (np.cos(dec0) * np.sin(dec) - np.sin(dec0) * np.cos(dec) * np.cos(ra - ra0)) / cosc
    return np.degrees(xi), np.degrees(eta)


def from_tangent(xi, eta, ra0, dec0):
    xi, eta, ra0, dec0 = map(np.radians, (xi, eta, ra0, dec0))
    rho = np.hypot(xi, eta)
    if rho == 0:
        return float(np.degrees(ra0)), float(np.degrees(dec0))
    c = np.arctan(rho)
    dec = np.arcsin(np.cos(c) * np.sin(dec0) + eta * np.sin(c) * np.cos(dec0) / rho)
    ra = ra0 + np.arctan2(xi * np.sin(c), rho * np.cos(dec0) * np.cos(c) - eta * np.sin(dec0) * np.sin(c))
    return float(np.degrees(ra) % 360), float(np.degrees(dec))


def render(cat, ra0, dec0, exposure=1.0, seed=None):
    """Camera frame for a scope truly pointing at (ra0, dec0)."""
    rng = np.random.default_rng(seed)
    ra, dec, mag = cat.cone(ra0, dec0, 2.5)
    xi, eta = to_tangent(ra, dec, ra0, dec0)
    x = W / 2 + xi / SCALE_DEG
    y = H / 2 - eta / SCALE_DEG
    img = rng.normal(100.0, 3.0, (H, W))
    yy, xx = np.mgrid[-5:6, -5:6]
    for xs, ys, m in zip(x, y, mag):
        if not (6 < xs < W - 6 and 6 < ys < H - 6):
            continue
        peak = 3000 * 10 ** (-0.4 * (m - 6)) * exposure
        ix, iy = int(round(xs)), int(round(ys))
        img[iy - 5:iy + 6, ix - 5:ix + 6] += peak * np.exp(
            -((xx - (xs - ix)) ** 2 + (yy - (ys - iy)) ** 2) / (2 * PSF_SIGMA ** 2))
    return np.clip(img, 0, 65535)


def detect(img, n=40):
    med = np.median(img)
    sigma = 1.4826 * np.median(np.abs(img - med))
    thr = med + 6 * sigma
    p = np.pad(img, 3, constant_values=0)
    local_max = np.ones_like(img, dtype=bool)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            local_max &= img >= p[3 + dy:3 + dy + H, 3 + dx:3 + dx + W]
    ys, xs = np.nonzero(local_max & (img > thr))
    gy, gx = np.mgrid[-3:4, -3:4]
    stars = []
    for x, y in zip(xs, ys):
        if 4 <= x < W - 4 and 4 <= y < H - 4:
            patch = np.clip(img[y - 3:y + 4, x - 3:x + 4] - med, 0, None)
            f = patch.sum()
            stars.append((x + (patch * gx).sum() / f, y + (patch * gy).sum() / f, f))
    stars.sort(key=lambda s: -s[2])
    return np.array(stars[:n])


def solve(img, hint_ra, hint_dec, radius=6.0, cat=None):
    """Plate-solve: find where the frame is really pointing, near the hint.
    Scale and orientation are known (a real solver fits those too).
    Returns (ra, dec, n_matched) or None."""
    stars = detect(img)
    if len(stars) < 6:
        return None
    cra, cdec, _ = cat.cone(hint_ra, hint_dec, radius)
    cxi, ceta = to_tangent(cra, cdec, hint_ra, hint_dec)
    dxi = (stars[:, 0] - W / 2) * SCALE_DEG
    deta = -(stars[:, 1] - H / 2) * SCALE_DEG
    ox = (cxi[None, :] - dxi[:, None]).ravel()      # candidate field-centre offsets
    oy = (ceta[None, :] - deta[:, None]).ravel()
    tol = 2 * SCALE_DEG
    bins = int(2 * radius / tol) + 1
    hist, ex, ey = np.histogram2d(ox, oy, bins=bins, range=[[-radius, radius]] * 2)
    s = hist[:-1, :-1] + hist[1:, :-1] + hist[:-1, 1:] + hist[1:, 1:]
    i, j = np.unravel_index(np.argmax(s), s.shape)
    cx, cy = (ex[i] + ex[i + 2]) / 2, (ey[j] + ey[j + 2]) / 2
    inl = np.hypot(ox - cx, oy - cy) < 2 * tol
    n = int(inl.sum())
    if n < 8:
        return None
    ra, dec = from_tangent(ox[inl].mean(), oy[inl].mean(), hint_ra, hint_dec)
    return ra, dec, n


def save_png(img, path):
    lo, hi = np.percentile(img, 1), np.percentile(img, 99.9)
    a = np.clip((img - lo) / (hi - lo), 0, 1)
    g = (a ** 0.5 * 255).astype(np.uint8)
    raw = b"".join(b"\x00" + g[r].tobytes() for r in range(g.shape[0]))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", g.shape[1], g.shape[0], 8, 0, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
