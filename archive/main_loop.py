"""
main_loop.py

Ties the three pieces together:
  1. Stellarium tells us where the object SHOULD be (predictive)
  2. coords.py converts that into Alt/Az pointing angles for our location
  3. OpenCV checks where the object ACTUALLY is in the camera frame (corrective)

This version has NO motor control yet - it just prints what it WOULD send
to the motors. That's intentional: get this loop working and printing
sensible numbers first, then swap print_motor_command() for real serial
commands to your ESP32/Arduino once the mechanical side is ready.

USAGE:
    python main_loop.py
"""

import time
import cv2

from stellarium_client import StellariumClient
from coords import SkyConverter
from detector import BrightObjectDetector

# ---- CONFIG: edit these for your setup ----
YOUR_LATITUDE = 12.9716    # Vellore, replace with your exact site if different
YOUR_LONGITUDE = 79.1325
TARGET_OBJECT_NAME = "Jupiter"   # anything Stellarium recognizes by name
CAMERA_INDEX = 0                 # 0 = default webcam; change if using a different camera
FOV_DEGREES = 1.0                # calibrate this for your actual optics (see note below)
LOOP_INTERVAL_SECONDS = 1.0      # how often to re-query Stellarium (coarse loop)
# --------------------------------------------


def pixel_offset_to_angle(offset_pixels: float, frame_dimension_pixels: int, fov_degrees: float) -> float:
    """
    Converts a pixel offset into a real-world angular offset, using the
    camera's calibrated field of view. This is the "one-time calibration"
    step mentioned earlier - FOV_DEGREES above is a placeholder until you
    measure your actual setup's field of view.
    """
    degrees_per_pixel = fov_degrees / frame_dimension_pixels
    return offset_pixels * degrees_per_pixel


def print_motor_command(alt_correction_deg: float, az_correction_deg: float, source: str):
    """
    Placeholder for real motor control. Replace this function's body with
    serial.write(...) calls to your ESP32/Arduino once wired up.
    """
    print(f"  [{source}] Would move -> Alt: {alt_correction_deg:+.4f} deg, Az: {az_correction_deg:+.4f} deg")


def run():
    print("Connecting to Stellarium...")
    stellarium = StellariumClient()
    try:
        stellarium.get_status()
    except Exception as e:
        print(f"Could not reach Stellarium ({e}). Make sure it's open with Remote Control server started.")
        return

    print("Loading sky converter (this downloads ephemeris data on first run)...")
    converter = SkyConverter(latitude_deg=YOUR_LATITUDE, longitude_deg=YOUR_LONGITUDE)

    print(f"Opening camera index {CAMERA_INDEX}...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    detector = BrightObjectDetector(brightness_threshold=200)
    have_camera = cap.isOpened()
    if not have_camera:
        print("No camera detected - running Stellarium-only (coarse loop only), no visual correction.")

    last_coarse_update = 0

    print(f"\nTracking '{TARGET_OBJECT_NAME}'. Press Ctrl+C to stop.\n")
    try:
        while True:
            now = time.time()

            # ---- COARSE LOOP: Stellarium prediction, ~once per second ----
            if now - last_coarse_update >= LOOP_INTERVAL_SECONDS:
                info = stellarium.get_object_info(TARGET_OBJECT_NAME)
                ra_deg = info.get("ra")
                dec_deg = info.get("dec")

                if ra_deg is not None and dec_deg is not None:
                    alt, az = converter.radec_to_altaz(ra_deg, dec_deg)
                    print(f"[Stellarium] {TARGET_OBJECT_NAME}: RA={ra_deg:.3f} Dec={dec_deg:.3f}  ->  Alt={alt:.3f} Az={az:.3f}")
                    print_motor_command(alt, az, source="COARSE")
                else:
                    print(f"Could not get coordinates for '{TARGET_OBJECT_NAME}'. Check the name matches Stellarium's catalog.")

                last_coarse_update = now

            # ---- FINE LOOP: OpenCV correction, every frame ----
            if have_camera:
                ret, frame = cap.read()
                if ret:
                    result = detector.find_brightest_object(frame)
                    if result["found"]:
                        h, w = frame.shape[:2]
                        alt_corr = -pixel_offset_to_angle(result["offset_y"], h, FOV_DEGREES)
                        az_corr = pixel_offset_to_angle(result["offset_x"], w, FOV_DEGREES)
                        print_motor_command(alt_corr, az_corr, source="FINE ")

                    debug_frame = detector.draw_debug_overlay(frame, result)
                    cv2.imshow("Tracking View", debug_frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        if have_camera:
            cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
