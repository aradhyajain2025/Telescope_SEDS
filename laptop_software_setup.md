# Telescope Software Stack: Laptop Setup Guide

Since you are treating the laptop software as a standalone milestone, we can get the entire astrophotography suite installed, configured, and simulated before the hardware is even finished.

The modern Windows astrophotography stack relies on **ASCOM** to act as a universal translator between the hardware and the software.

Here is the exact installation order. **Do not skip around**, as later software depends on the earlier layers being present!

## 1. The ASCOM Platform (The Core Hub)

ASCOM is the driver framework that allows N.I.N.A. to talk to your OnStep mount without knowing anything about OnStep specifically.

1. Download the latest **ASCOM Platform** from: [ascom-standards.org](https://ascom-standards.org/)
2. Run the installer and accept all default settings.

## 2. The OnStep ASCOM Driver

This is the specific plugin that teaches the ASCOM platform how to translate generic telescope commands into the specific serial/WiFi commands that the OnStep firmware understands.

1. Download the **OnStep ASCOM Driver** from: [http://www.stellarjourney.com/index.php?r=site/software_telescope](http://www.stellarjourney.com/index.php?r=site/software_telescope)
2. Install it. (It won't appear as a standalone app; it runs in the background when requested).

## 3. N.I.N.A. (Nighttime Imaging 'N' Astronomy)

This is your main interface. You will use N.I.N.A. to control everything: slewing the mount, taking pictures, plate solving, and running automated overnight sequences.

1. Download the **N.I.N.A. 3.0 (Nightly or Beta)** from: [nighttime-imaging.eu](https://nighttime-imaging.eu/)
2. Run the installer.

## 4. ASTAP (The Plate Solver)

Plate solving is what replaces the OpenCV computer-vision script. ASTAP will take a photo from your camera, analyze the star patterns, compare them against a massive offline database, and tell N.I.N.A. the exact RA/Dec coordinates the telescope is currently pointed at.

1. Download the **ASTAP Installer** from: [hnsky.org/astap.htm](https://www.hnsky.org/astap.htm) (Look for the Windows 64-bit version).
2. Install it.
3. **CRITICAL STEP**: On the same download page, download the **D80 Star Database**. This is a ~1GB file containing the star catalog. ASTAP cannot function without it. Run its installer after ASTAP finishes.

## How to Test Without Hardware

You don't need the ESP32 to verify that this setup works! 
1. Open N.I.N.A.
2. Go to the **Equipment > Telescope** tab.
3. In the dropdown, you should see "OnStep Telescope" (this proves the driver installed correctly).
4. If you want to play around with N.I.N.A. without the mount, you can select the **"Telescope Simulator for .NET"** from the dropdown, click the Connect icon, and practice slewing around the Sky Atlas!
