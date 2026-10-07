# Phase 4: Simulating the Hardware in N.I.N.A.

Since the physical telescope and ESP32 board are still in the design phase, the best way to get familiar with your new software stack is to use N.I.N.A.'s built-in simulators. 

This allows you to learn how to frame objects, slew, and plate-solve from your laptop right now.

## 1. Connecting to the Simulators

Open N.I.N.A. and click on the **Equipment** tab on the left sidebar.

### 1a. Simulate the Camera
1. Click the **Camera** icon.
2. From the dropdown, select **Camera Simulator**.
3. Click the Power icon (Connect) on the right. You should see a green success message.

### 1b. Simulate the Telescope (Mount)
1. Click the **Telescope** icon.
2. From the dropdown, select **Telescope Simulator for .NET** (this is a built-in ASCOM simulator).
3. Click the Power icon (Connect). 

> [!NOTE]
> Once your hardware is built, you will come back to this exact dropdown and select **OnStep Telescope** instead, then click the gear icon to put in your ESP32's COM port or IP address.

## 2. Using the Sky Atlas (Replacing Stellarium)

Now that N.I.N.A. thinks it is connected to a real telescope and camera, you can practice targeting.

1. Click the **Sky Atlas** tab on the left sidebar.
2. Search for a famous object (e.g., `M42` for the Orion Nebula, or `Jupiter`).
3. Click on the object in the search results.
4. In the bottom right corner, click **Set for Framing**.

## 3. The Framing Assistant

The Framing Assistant will load an actual image of that part of the sky. 
- The rectangle on the screen represents your camera's field of view. 
- You can drag it around to perfectly frame the nebula or planet exactly how you want it.

When you are happy with the framing, look at the buttons at the bottom right. 
Click **Slew and Center**.

## 4. What Happens Next (The Magic)

When you click "Slew and Center", N.I.N.A. will execute the exact same loop we were trying to build in Python:

1. It sends the target RA/Dec coordinates to the Telescope Simulator (GoTo).
2. It waits for the mount to finish moving.
3. It takes a picture using the Camera Simulator.
4. It sends that picture to **ASTAP** (the plate solver).
5. ASTAP figures out exactly where the telescope *actually* ended up.
6. If the telescope missed the target by a few pixels, N.I.N.A. automatically calculates the offset and sends a tiny correction command to the mount to perfectly center the object.

Go ahead and play around with the simulators! Familiarizing yourself with the N.I.N.A interface now will make connecting the real ESP32 extremely smooth later.
