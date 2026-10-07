"""
coords.py

Converts RA/Dec (sky coordinates) into Alt/Az (real-world pointing angles)
for YOUR specific location, using skyfield.

This is Step 2 from our earlier conversation, made concrete.
"""

from skyfield.api import load, wgs84, Star
from skyfield.units import Angle


class SkyConverter:
    def __init__(self, latitude_deg: float, longitude_deg: float, elevation_m: float = 0):
        """
        latitude_deg / longitude_deg: your observing location.
        Example for Vellore, Tamil Nadu: latitude=12.9716, longitude=79.1325
        """
        self.ts = load.timescale()
        self.observer = wgs84.latlon(latitude_deg, longitude_deg, elevation_m)

        # Downloads ~17MB the first time it's run, then caches locally.
        self.eph = load("de421.bsp")
        self.earth = self.eph["earth"]

    def radec_to_altaz(self, ra_deg: float, dec_deg: float):
        """
        ra_deg: Right Ascension in DEGREES (convert from hours by * 15 if needed)
        dec_deg: Declination in DEGREES

        Returns: (altitude_deg, azimuth_deg)
        """
        t = self.ts.now()
        ra_hours = ra_deg / 15.0

        star = Star(ra_hours=ra_hours, dec_degrees=dec_deg)
        astrometric = (self.earth + self.observer).at(t).observe(star)
        alt, az, _distance = astrometric.apparent().altaz()

        return alt.degrees, az.degrees

    def altaz_rate_of_change(self, ra_deg: float, dec_deg: float, dt_seconds: float = 1.0):
        """
        Returns how fast Alt and Az are currently changing, in degrees/second,
        for a fixed sky object. Useful for driving motors at the correct
        continuous speed rather than just snapping to a position.
        """
        from datetime import timedelta

        t1 = self.ts.now()
        t2 = self.ts.from_datetime(t1.utc_datetime() + timedelta(seconds=dt_seconds))

        ra_hours = ra_deg / 15.0
        star = Star(ra_hours=ra_hours, dec_degrees=dec_deg)

        alt1, az1, _ = (self.earth + self.observer).at(t1).observe(star).apparent().altaz()
        alt2, az2, _ = (self.earth + self.observer).at(t2).observe(star).apparent().altaz()

        alt_rate = (alt2.degrees - alt1.degrees) / dt_seconds
        az_rate = (az2.degrees - az1.degrees) / dt_seconds

        return alt_rate, az_rate


if __name__ == "__main__":
    # Quick manual test with a known bright star, Vega, so you don't
    # need Stellarium running to sanity-check this file alone.
    # Vega: RA = 18h 36m 56s -> ~279.23 deg, Dec = +38.78 deg
    converter = SkyConverter(latitude_deg=12.9716, longitude_deg=79.1325)
    alt, az = converter.radec_to_altaz(ra_deg=279.23, dec_deg=38.78)
    print(f"Vega right now from Vellore: Altitude={alt:.2f} deg, Azimuth={az:.2f} deg")

    alt_rate, az_rate = converter.altaz_rate_of_change(ra_deg=279.23, dec_deg=38.78)
    print(f"Tracking rate needed: Alt {alt_rate*3600:.4f} arcsec/sec, Az {az_rate*3600:.4f} arcsec/sec")
