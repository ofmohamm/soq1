# SOQ1

A privacy-first acoustic tracking system. It finds the direction of a sound source from a microphone array and points a servo at it, without recording audio or sending anything off the machine.

### Features

- **Local only** : audio never leaves the machine. Capture, processing, and display all run on the host.
- **Direction, not content** : the estimator throws away everything except phase, so no speech or other audio information is captured. 
- **Nothing written to disk** : frames are processed in memory and immediately discarded. 
- **Stable under rotation** : fusing the acoustic estimate with IMU heading gives a bearing in world coordinates as the platform turns.
- **Live visualizer** : a Qt desktop UI shows the direction in real time.

https://github.com/user-attachments/assets/730054fe-5365-48c3-b036-a59ecac2e4ce

## How it works

<img width="845" height="654" alt="image" src="https://github.com/user-attachments/assets/12e65b35-52e2-4d48-9f5d-b5b0b3a60d77" />

**Time delay of arrival**

- A sound reaching two microphones hits the closer one first, and that tiny delay tells you where it came from. 
- The Kinect has four mics. I use the outer pair, as a wider baseline means a bigger delay for the same angle, which improves accuracy. 
- Convert the delay with `sin(theta) = (tau * c) / d`, where c is 343 m/s and d is the 22.6 cm baseline.
- Zero degrees is straight ahead, negative is left, positive is right.

**GCC-PHAT**

- Measuring the delay is the hardest part. Plain cross-correlation doesn't operate as well in a normal room, as reflections get picked up as new sources.
- GCC-PHAT takes the cross-power spectrum of the two channels and divides it by its own magnitude. 
- It flattens the spectrum so every frequency contributes equally, which sharpens the correlation peak and recognizes the reverberations as noise.
- It also discards loudness. Only the phase relationship between the two mics survives into the estimate, which is why the system can track you without capturing what you said.

**Input conditioning**

- Bandpass 300 to 3000 Hz. Covers speech and claps, rejects HVAC hum on the low end and hiss on the high end.
- RMS energy gate skips quiet frames, so the system stops chasing the correlation of room noise when nobody is talking.
- Lag search bounded to physically possible delays, plus or minus d/c. Throws out a whole class of spurious peaks for free.
- Exponential moving average on the angle output, so the servo tracks instead of twitching.

**IMU Header**

- An acoustic array only measures direction relative to where it is currently facing, which stops being useful the moment the rig starts moving.
- The BNO055 reports absolute heading over serial in the range 0 to 360.
- Fusing that with the acoustic estimate gives a bearing in world coordinates that stays correct while the platform rotates.
- The same microcontroller that reports heading also drives the pan servo, so sensing and actuation live on one board.

**Process architecture**

- Three processes, two hops. A C capture program built on libfreenect streams four channels of audio to stdout.
- The Python processor reads that off an ordinary pipe, then sends telemetry to the visualizer over loopback UDP.
- The visualizer can be attached, detached, or restarted without touching capture or servo control.
- A dropped datagram degrades the display instead of stalling the control loop. For soft-real-time telemetry that tradeoff is the right one.

## Notes

- A linear array cannot tell front from back. A source at +theta in front produces the same delays as one at +theta behind, so the geometry has to be known ahead of time.
- Channel order matters more than it looks. If the mic indices are mirrored relative to physical position, every angle comes out mirrored.
- The only way to catch that is to clap from a known side and check the sign before trusting anything downstream.

Credit: [Quintin Hatzis](https://www.linkedin.com/in/quintinhatzis/) and [Sawyer Falkenbush](https://www.linkedin.com/in/sawyer-falkenbush/) for collaborating with me on this project

