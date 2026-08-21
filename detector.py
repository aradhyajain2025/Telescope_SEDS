"""
detector.py

Uses OpenCV to find the brightest object in a camera frame and return
its pixel offset from the frame center. No ML needed for this - simple
thresholding + centroid is the standard approach for point-source
tracking (stars, planets, Moon).
"""

import cv2
import numpy as np


class BrightObjectDetector:
    def __init__(self, brightness_threshold: int = 200, min_area: int = 3):
        """
        brightness_threshold: pixel value (0-255) above which something
            counts as "the object". Raise this if you're picking up noise
            or light pollution; lower it if you're missing faint objects.
        min_area: minimum blob size in pixels, to reject single hot pixels
            or sensor noise.
        """
        self.threshold = brightness_threshold
        self.min_area = min_area

    def find_brightest_object(self, frame: np.ndarray):
        """
        frame: a BGR image (as returned by cv2.VideoCapture.read())

        Returns: dict with 'found' (bool), and if found:
            'cx', 'cy' (centroid pixel coords),
            'offset_x', 'offset_y' (pixels from frame center),
            'area' (blob size in pixels)
        Returns 'found': False if nothing passed the filters.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, self.threshold, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates = [c for c in contours if cv2.contourArea(c) >= self.min_area]
        if not candidates:
            return {"found": False}

        # Pick the largest blob as "the object" (works well when there's
        # one dominant bright thing in frame, e.g. Moon, a planet, Jupiter)
        largest = max(candidates, key=cv2.contourArea)

        moments = cv2.moments(largest)
        if moments["m00"] == 0:
            return {"found": False}

        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"]

        frame_h, frame_w = frame.shape[:2]
        offset_x = cx - (frame_w / 2)
        offset_y = cy - (frame_h / 2)

        return {
            "found": True,
            "cx": cx,
            "cy": cy,
            "offset_x": offset_x,
            "offset_y": offset_y,
            "area": cv2.contourArea(largest),
        }

    def draw_debug_overlay(self, frame: np.ndarray, result: dict) -> np.ndarray:
        """Draws a crosshair on the detected object and frame center, for visual testing."""
        debug = frame.copy()
        h, w = frame.shape[:2]
        cv2.drawMarker(debug, (w // 2, h // 2), (0, 255, 0), cv2.MARKER_CROSS, 20, 1)

        if result.get("found"):
            cx, cy = int(result["cx"]), int(result["cy"])
            cv2.drawMarker(debug, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
            cv2.putText(debug, f"offset: ({result['offset_x']:.0f}, {result['offset_y']:.0f})",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.putText(debug, "no object detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

        return debug


if __name__ == "__main__":
    # Quick manual test using your laptop webcam (won't detect stars,
    # but confirms the pipeline works - point it at a bright lamp in a dark room).
    detector = BrightObjectDetector(brightness_threshold=200)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("No camera found. Skipping live test.")
    else:
        print("Press 'q' to quit.")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            result = detector.find_brightest_object(frame)
            debug_frame = detector.draw_debug_overlay(frame, result)
            cv2.imshow("Bright Object Detector - Test", debug_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        cap.release()
        cv2.destroyAllWindows()
