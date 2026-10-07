# ASTAP layer: status summary

**Bottom line:** ASTAP works from the command line and agrees with ground truth to about 10-20 arcsec when it solves. On Stellarium test images it solved correctly **43 of 56** times. It sometimes returns confident *wrong* answers, so the closed loop needs safeguards. Real camera images are untested.

## Done
- ASTAP (CLI version 2026.07.30) and the full D80 database are installed (`C:\Program Files\astap\astap_cli.exe`).
- Stellarium Remote Control is working. Ground truth is read from Stellarium's `raJ2000`/`decJ2000` (plain `ra`/`dec` are of-date and differ by ~20 arcmin; some J2000 RAs are negative and must be wrapped).
- Tool: `astap_test.py` solves an image and prints the error against Stellarium's true position.
- Batch: `batch.py` made 56 screenshots (14 targets x 0.7/1/2/4 deg fields); `diagnose.py` retried them with six ASTAP settings. Results: `results.csv`, `diagnose_output.txt`.

## Findings
1. **Command that works:** `astap_cli -f img.png -fov <image HEIGHT in deg> -ra <hours> -spd <dec+90> -r 8 -t 0.02`. Stellarium's FOV is the image height, and so is ASTAP's `-fov` in practice (2 deg gave 4.50 arcsec/px x 1600 px).
2. **Quad tolerance:** the default `-t 0.007` failed on every Stellarium image; `-t 0.02` works. Looser values (0.03 with more stars, wider search, slow mode) were worse: 23-25 correct versus 43.
3. **Accuracy:** good solves are 6-30 arcsec from truth, steady regardless of field size. Probably Stellarium's own offset (aberration is my guess, unverified).
4. **Reliability by field:** 4 deg solved 14/14 in the first batch; smaller fields (0.7, 1, 2 deg) failed more often. Seven images never solved: M45, M13, M31 at most sizes, Spica at 0.7/1 deg, Betelgeuse at 0.7/2 deg. Cause not verified (guess: nebula/cluster textures or sparse fields).
5. **False solutions:** ASTAP reports `PLTSOLVD=T` for wrong answers. One had a scale of 29 arcsec/px instead of 1.58 (error 8.7 deg). Others had the right scale in the wrong place.
6. Solve time: 0.5-2.6 s.

## Needed in the closed loop
- Reject any solution whose scale differs >10% from the expected scale (already in `astap_test.py`).
- Reject any solution far from the mount's reported position (not implemented; belongs to the loop).
- Treat "no solution" as normal: retry with a longer exposure or a different field rather than loosening ASTAP settings.

## Caveats
- Test images are Stellarium renderings, not camera frames. Noise, star shapes and brightness differ; `-t` and the database choice must be re-checked with real frames.
- The results vary with the starting hint (some images changed between runs), so treat 43/56 as approximate.

## Need from the team
- Camera pixel size, sensor size and the telescope focal length (gives the real field of view, which decides the database and `-fov`).
- The scope of the Python layer: parse ASTAP output, pointing error, closed-loop simulation?
