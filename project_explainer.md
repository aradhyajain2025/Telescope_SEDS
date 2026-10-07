# Telescope Automation: Full Project Explainer

If you need to present this project, defend its design decisions, or just understand exactly how the pieces fit together from scratch, this document covers everything. It explains what we built, why we chose the tools we did, and how the entire system functions as a cohesive unit.

---

## 1. The Goal
The objective is to take a **Dobsonian Telescope**, mount it on a **Poncet Platform**, and fully automate it so it can locate celestial objects (GoTo) and track them perfectly for long-exposure astrophotography. 

By placing the Dobsonian on a Poncet platform, we mechanically converted an Alt-Azimuth mount (which requires complex 2-axis variable tracking) into an **Equatorial mount** (which only requires a single motor moving at a constant speed to cancel out the Earth's rotation).

---

## 2. The Evolution of the Software Design

### The Initial Idea (Custom Python Stack)
Initially, we started writing custom Python scripts:
- `stellarium_client.py`: To ask the Stellarium app for the coordinates of a planet.
- `coords.py`: To do trigonometry to figure out where those coordinates are in the real sky.
- `detector.py`: Using **OpenCV** to look through a camera, find the brightest white blob (a star), and calculate how far it drifted from the center of the frame.
- `main_loop.py`: To tie it all together and send correction signals to motors.

### Why We Scrapped It
While writing a custom Python loop is a great coding exercise, it is terrible for actual astrophotography. OpenCV looking for a "bright blob" gets easily confused by clouds, airplanes, or multiple stars in the same field of view. 

Instead, we pivoted to an **Industry-Standard Stack**. We replaced our fragile Python scripts with the exact same open-source software that professional observatories and advanced amateur astrophotographers use.

---

## 3. The New Architecture (How It Works Now)

The system is split into two halves: **Hardware (The Mount)** and **Software (The Laptop)**.

### A. The Hardware (OnStep Firmware)
The "brain" attached to the telescope is an **ESP32 microcontroller** (specifically the WeMos D1 R32). It sits on a **CNC V3 Shield**, which routes power to our stepper motors.
- We flashed the ESP32 with an open-source firmware called **OnStep**.
- OnStep is designed specifically for telescopes. It handles all the intense celestial math locally on the chip. 
- **The Stepper Drivers**: We specified **TMC2209** stepper drivers running at 64-microsteps. This is critical. Standard 3D printer drivers (like the DRV8825) vibrate slightly when they step. For astrophotography, that vibration blurs the stars. TMC2209s use "StealthChop" technology to make the motors completely silent and vibration-free.
- **The Math**: We wrote a calculator (`config_calculator.py`) to figure out the `AXIS1_STEPS_PER_DEGREE`. By looking at the motor's step angle (1.8°), the microstepping (64), and the physical gear ratio of the Poncet platform, we taught the ESP32 exactly how many electrical pulses it takes to move the telescope exactly one degree across the sky.

### B. The Translator (ASCOM)
Telescopes, cameras, and focusers all speak different digital languages. To solve this, we installed the **ASCOM Platform** on the Windows laptop. ASCOM acts as a universal translator. 
Our software doesn't need to know how to speak to an ESP32; it just speaks "ASCOM," and the ASCOM OnStep Driver translates that into serial pulses for the ESP32.

### C. The Commander (N.I.N.A.)
**N.I.N.A. (Nighttime Imaging 'N' Astronomy)** replaces our old `main_loop.py` and Stellarium. It is the central command hub on the laptop. 
- N.I.N.A. contains a Sky Atlas. You search for a target (like the Orion Nebula), and click "Slew". 
- N.I.N.A. sends the ASCOM command, and the ESP32 drives the motors to that target.

### D. The Eyes (ASTAP Plate Solving)
This replaces our OpenCV script. When the telescope stops moving, we need to know if it is *actually* pointing at the target, or if the gears slipped slightly.
- N.I.N.A. takes a picture through the telescope camera and hands it to **ASTAP**.
- ASTAP looks at the pattern of the stars in the photo (like a fingerprint) and compares it against a massive 1GB offline database (the D80 catalog) at lightning speed. 
- ASTAP replies: *"Based on the stars in this image, the telescope is actually pointing at RA 05h 35m, Dec -05° 23'."*
- If the telescope missed by a few pixels, N.I.N.A. automatically calculates the offset and tells the ESP32 to bump the motors slightly to center it perfectly. This is known as **Closed-Loop Plate Solving**.

---

## 4. How to Demonstrate This With Zero Hardware

Because we used standard software (N.I.N.A. and ASCOM) instead of hardcoding python to a specific USB port, the entire system is modular. 

We can completely fake the hardware to prove the software logic works:
1. Inside N.I.N.A., instead of connecting to the OnStep driver, we select the **Telescope Simulator** and **Camera Simulator**. 
2. When we ask N.I.N.A. to slew to a target, the Simulator pretends to move and updates its virtual coordinates.
3. When N.I.N.A. asks for a picture, the Camera Simulator generates a fake image of the night sky based on where the virtual telescope is pointing.
4. N.I.N.A. passes that fake image to ASTAP, which plate-solves it successfully, proving the entire closed-loop tracking system functions perfectly on the laptop before a single motor is ever wired up.
