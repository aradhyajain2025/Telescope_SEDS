# SEDS VIT Telescope: Automatic Object Tracking

Goal: restore one of our broken Dobsonian telescopes and give it automatic motion that can find a planetary object (for example Jupiter) and keep it centered. Deadline for a working demo: end of August / first week of September.

The project has three phases: literature, design, and gradual restoration. This repo is the **software** side. Hardware (motors, ESP32 running OnStep firmware, ASCOM driver) is handled later and is out of scope for now.

## How the system fits together

1. **Where should the object be?** Stellarium and Skyfield give the predicted RA/Dec, converted to Alt/Az for our site and the current time.
2. **Point there.** The mount slews to that position (hardware, later).
3. **Where is the telescope actually pointing?** A photo is taken, and ASTAP plate solves it: it matches the star pattern against an offline star database and returns the true RA/Dec of the frame center.
4. **Correct the difference.** N.I.N.A. computes the offset between target and solved position and re-centers.
5. Repeat. In practice, "locking on" means periodic re-solving and re-centering, with the mount's tracking rate doing the work in between. It is not frame by frame correction.

Tools: **N.I.N.A.** is the command hub (sky atlas, slew, center). **ASTAP** is the plate solver. **ASCOM and OnStep** are the hardware link, ignored for now.

## Roles

### Teammate: ASTAP and Python layer
You are the stronger Python developer, so you own everything around ASTAP and our existing Python code.

Confirmed tasks:
1. Install ASTAP and the star database that matches our field of view (check ASTAP's documentation for which database fits which field size).
2. Solve a test image from the command line. Syntax, per the ASTAP docs: `astap -f image.png -fov <field height in degrees> -ra <hours> -spd <dec + 90> -r <search radius in degrees>`. The `-fov`, `-ra` and `-spd` flags are only needed for non-FITS files, and command line values override FITS header values.
3. Build ground truth test images. Take screenshots of a star field in Stellarium. Stellarium's RemoteControl API (`/api/objects/info?format=json`) reports the true position, so you know the right answer before ASTAP gives its own.
4. Read `coords.py` and `stellarium_client.py` (see repo map below) so you understand what already exists.

**To be decided:** the exact scope of the Python layer (for example whether to parse ASTAP output, compute pointing error, or simulate a closed loop without hardware). Aradhya will define this once the plan is clear. Do not start on it yet.

### Aradhya: N.I.N.A. layer
1. Install N.I.N.A. and connect its built in simulator camera and mount (no hardware or ASCOM needed).
2. Enter camera pixel size and telescope focal length. N.I.N.A. passes these to ASTAP, so wrong values break solving. Use placeholders until we measure the real optics.
3. Point N.I.N.A.'s plate solver settings at the ASTAP install.
4. Pick a target in the Sky Atlas, slew in the simulator, and run a slew and center with a test image.
5. Record every setting that worked in the shared parameters sheet.

## Sync points

1. Both of us solve the **same test image**, one through the command line and one inside N.I.N.A. The answers should match. If not, check focal length, pixel size and FOV inputs first.
2. One shared parameters sheet: latitude/longitude, focal length, pixel size, FOV, ASTAP database, search radius.
3. A joint decision: N.I.N.A. alone, or N.I.N.A. plus a custom Python layer.

## Repo map

| File | Status | What it does |
|---|---|---|
| `coords.py` | Reuse | Converts RA/Dec to Alt/Az for our site with Skyfield, using apparent positions. |
| `stellarium_client.py` | Reuse | Talks to Stellarium's RemoteControl HTTP API (select object, read info as JSON). |
| `detector.py` | Reference only | OpenCV threshold, contour and centroid detection. Replaced by ASTAP in the new plan, but shows the earlier approach. |
| `main_loop.py` | Reference only | Earlier integration loop (coarse Stellarium prediction plus fine OpenCV correction), prints instead of driving motors. |
| `de421.bsp` | Data file | NASA JPL ephemeris data. It is not run. `coords.py` loads it to know where Earth is. |
| `requirements.txt` | Setup | `opencv-python`, `requests`, `skyfield`, `numpy`. |

## Prerequisites

* Windows, Python 3.10 or newer
* `pip install -r requirements.txt`
* Stellarium with the Remote Control plugin enabled and its server started (default `http://localhost:8090`)
* First run of `coords.py` downloads `de421.bsp` if it is missing

## Verify, don't assume

* Print the **full** Stellarium JSON for an object before writing code against it. Different object types return different keys.
* Stellarium's location must be set to our real site and its simulation time must be synced to real time, or Alt/Az values are wrong.
* `FOV_DEGREES` in `main_loop.py` is an unmeasured placeholder.
* `cv2.findContours` in `detector.py` expects the OpenCV 4 return signature (two values). Check your installed version if it errors.

## Glossary

* **RA/Dec:** sky coordinates (like longitude/latitude on the celestial sphere). Apparent RA/Dec includes real world corrections and is what we use for pointing.
* **Alt/Az:** angle above the horizon and compass direction from our site. This is what the mount understands.
* **Plate solving:** identifying where a photo is pointing by matching its star pattern to a catalog.

## Sources

* ASTAP: https://www.hnsky.org/astap.htm
* N.I.N.A. plate solving: https://nighttime-imaging.eu/docs/master/site/advanced/platesolving/
* Skyfield positions: https://rhodesmill.org/skyfield/positions.html
* Stellarium RemoteControl API: https://stellarium.org/doc/head/remoteControlApi.html
