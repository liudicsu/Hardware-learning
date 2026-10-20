# Line follower

My line following robot! It works really well and is very fast.

![robot](robot.gif)

## Hardware

Arduino Nano, two TT motors with an L298N driver, a 5-channel IR sensor array, 2 x 18650 cells.

## Code

The code is in line_follower.ino. Upload it with the Arduino IDE.

## Tuning

I tuned kp, ki and kd until it worked. Final values: kp = 0.8, ki = 0, kd = 4.
