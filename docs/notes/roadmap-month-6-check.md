# Month 6 resources vs. the roadmap post

Checked 2026-10-20 (UTC+8). The post (x.com/DeRonin_/status/2095180126359105955) is an X article and
was unreadable earlier. nitter.net now returns a bot-check page, nitter.poast.org / nitter.privacydev.net
do not answer, xcancel.com returns 451 and nitter.space 403. The public fxtwitter API
(`https://api.fxtwitter.com/DeRonin_/status/2095180126359105955`) returns the full article
("How to become a Robotics Engineer in 6 months (RESOURCES)", published 2026-09-03 00:00 UTC+8), including
the section "Month 6: Robot learning, specialisation, and becoming hireable".

## Resources the post lists for Month 6

| Post section | Resource (link in the post) | On the site |
|---|---|---|
| 1. LeRobot | LeRobot documentation (`huggingface.co/docs/lerobot/index`) | `lerobot-il-robots` is a page of these docs → **no longer `extra`** |
| 1. LeRobot | LeRobot repository (`github.com/huggingface/lerobot`) | no card |
| 1. LeRobot | Hugging Face Robotics Course (`huggingface.co/learn/robotics-course/unit0/1`) | no card |
| 1. LeRobot | SO-101 setup guide (`huggingface.co/docs/lerobot/so101`) | already a Month 3 card (not extra) |
| 2. VLA models | openpi: π0, π0-FAST, π0.5 (`github.com/Physical-Intelligence/openpi`) | `openpi`, same URL → **no longer `extra`** |
| 2. VLA models | OpenVLA (`openvla.github.io`) | `openvla`, same URL → **no longer `extra`** |
| 2. VLA models | GR00T N1.7 (`github.com/Nvidia/Isaac-GR00T`) | named in the lesson 3 licence table, no card |
| 2. VLA models | SmolVLA (`huggingface.co/lerobot/smolvla_base`) | `lerobot-smolvla` links the LeRobot SmolVLA docs page for the same model → **no longer `extra`** |
| 2. VLA models | RT-2 (no link; no public weights) | mentioned in lesson 3 |
| 3. RL for robotics | MuJoCo Playground, NVIDIA Isaac Lab, CS 285 (Berkeley) | no cards (Month 6 has no RL lesson) |
| 5. Interviews | Glassdoor robotics engineer interview questions | no card |

Still `extra` (our supplements, not in the post): `dagger-paper`, `act-paper`, `diffusion-policy`.
The post discusses ACT and Diffusion Policy as topics but links no paper or project page for them.
Cards reused from earlier months (`beauregard-pid`, `slam-toolbox`) keep the flag they already had.

Possible follow-up (not done here): cards for the LeRobot repository, the Hugging Face Robotics Course,
Isaac-GR00T, and the RL resources (MuJoCo Playground, Isaac Lab, CS 285). An RL lesson or supplement would be the natural place for the RL ones.
