# 11.7 contact-rich-policies

`tactile_gate_toy.py` — 1-D peg insertion: vision-only vs vision + gated tactile correction, and a swapped skin with an uncalibrated gain (stdlib).
AnySkin insertion numbers printed alongside are **paper constants** (arXiv 2409.08276), not toy measurements.
No tactile sensor purchase is required; on-robot tactile collection and policy training are not run on this page.

`contact_slip_residual_toy.py` — planar 2-link fingertip vs object: residual `v_meas − J(q)·qdot` compares two velocities in the same world frame and unit (m/s), never N − m/s. Contact break comes only from an assumed normal-force contact-flag channel; slip is a toy proxy (windowed tangential residual), not a GelSight / AnySkin classifier. Stick / slip / break share one seeded noise stream. Contact-Jacobian background: 11.6 `floating_base_contact_toy.py`.

`fdvla_force_distill_toy.py` — stdlib CPU linear / lookup stand-in: vision-only vs a distilled / predicted force token used at test time without the true force channel vs a noisy, biased, drop-out raw-sensor injection (shared contact-rich scenes, vision/state features and true latent force; common random numbers, five seeds). An unofficial clean oracle-force arm is printed for comparison and is not a retuning target. Not FD-VLA weights and not a real F/T sensor. Paper physical-experiment success rates and the distilled-beats-sensor claim 以论文为准, not toy outputs. Expected stdout: `../expected/fdvla_force_distill_toy.txt`; run `bash examples/month-11/check.sh` from the repo root. GPU / F/T hardware: 本页未运行.
