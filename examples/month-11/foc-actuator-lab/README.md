# 11.2 foc-actuator-lab

`clarke_park_toy.py` — Clarke–Park round-trip (algebraic identity; stdlib).
`foc_current_loop_toy.py` — electrical angle + dq PI on an **R–L circuit** plant
(NOT reinforcement learning); plant `theta_e_star` is never fed to the controller.
Optional SimpleFOC open-loop flash on an existing ESP32 is **not run here**
(needs a driver board; do not buy a BLDC kit for this lesson).
