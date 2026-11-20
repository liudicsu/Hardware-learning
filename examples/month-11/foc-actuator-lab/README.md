# 11.2 foc-actuator-lab

`clarke_park_toy.py` — Clarke–Park round-trip (algebraic identity; stdlib).
`foc_current_loop_toy.py` — electrical angle + dq PI on an **R–L circuit** plant
(NOT reinforcement learning); plant `theta_e_star` is never fed to the controller.
Optional SimpleFOC open-loop flash on an existing ESP32 is **not run here**
(needs a driver board; do not buy a BLDC kit for this lesson).
`foc_dq_decoupling_toy.py` — current-mode d/q cross-coupling feedforward
on a coupled dq plant (PI-only vs official feedforward vs wrong-sign;
voltage-mode lag alternative printed, not adopted). The earlier R–L
current-loop toy is unchanged and still omits coupling on both arms.
Official SimpleFOC flash is **not run here**.
