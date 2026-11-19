# Batch-25 PR1 sources

Base `def8795172af98816d18a7c732ac33b2066f8ea3` (batch-24 polish #200 merged; 71 lessons, site **42300**). This PR: **M4 3570→3750**, **M5 3750→3930**, site **42300→42660** (42660=42300+180+180), still 71 lessons. Hosts: `ros2-setup` 360→**540**, `kinematics-ik` 750→**930**.

## Opened sources

- ROS 2 documentation, Working with Zenoh, kilted branch, https://github.com/ros2/ros2_documentation/blob/kilted/source/Installation/RMW-Implementations/Non-DDS-Implementations/Working-with-Zenoh.rst, git `c16e4499d67f350e22dfec987a289e6e59ce506c` (2025-05-02 13:40 UTC = 2025-05-02 21:40 Asia/Shanghai). Body read. `export RMW_IMPLEMENTATION=rmw_zenoh_cpp`, `sudo apt install ros-{DISTRO}-rmw-zenoh-cpp`, `ros2 run rmw_zenoh_cpp rmw_zenohd`. Quote: “Without the Zenoh router, nodes will not be able to discover each other since multicast discovery is disabled by default in the node's session config. Instead, nodes will receive discovery information about other peers via the Zenoh router's gossip functionality.” sha256 `2da34ea7a589f7ab569f9a0f099dddd406a1f4b4b55dd7c654c2c408a9c6edfd`.
- Same path on the jazzy branch, git `1b19bccd1317223f5dab53b495426f177fdcddda` (2025-05-02 13:40 UTC). Body read; byte-identical to the Kilted page (same sha256). The page existing is not a claim that Jazzy binary releases package rmw_zenoh_cpp as Tier 1.
- ROS 2 documentation, About Different Middleware Vendors, kilted branch, https://github.com/ros2/ros2_documentation/blob/kilted/source/Concepts/Intermediate/About-Different-Middleware-Vendors.rst, git `17d097028c3a8dd09725ea3ceeaba2a9db103c35` (2026-04-26 14:57 UTC = 2026-04-26 22:57 Asia/Shanghai). Body read. Fast DDS (`rmw_fastrtps_cpp`) is the default RMW, packaged with binary releases. “Zenoh offers a more lightweight alternative to DDS and maintains Quality of Service features (in Zenoh, there are essentially no ‘incompatible’ QoS settings).” rmw_zenoh_cpp “Packaged with binary releases starting with Kilted Kaiju.” “Beginning with ROS 2 Kilted Kaiju, this also includes Eclipse Zenoh.” Default remains Fast DDS. sha256 `60e6854ff11db5f1d116eb567e4a18d98c85f059f8d391872f5fbaffa083a4f8`.
- Same path on the jazzy branch, git `95dbbf32761f6dfca6e6f6327a3a2cfb9784a653` (2025-05-20 18:13 UTC = 2025-05-21 02:13 Asia/Shanghai). Body read. Fast DDS default, packaged with binary releases. Zenoh is not listed in the packaged-RMW table. Binary releases listed: Fast DDS, RTI Connext Pro, Eclipse Cyclone DDS, GurumNetworks GurumDDS. sha256 `b2e7aa685fb08c2d164b76e80c78beba8f893fb0fa8451c1197e11100518aead`.
- ROS 2 documentation, Release Kilted Kaiju, kilted branch, fetched from that branch; latest GitHub commit touching the path as of fetch is `1f757343c8ed06b57896b5a5febc536919b10e7f` (2026-05-22T16:56:11Z = 2026-05-23 00:56 Asia/Shanghai). Body read. Middleware table: `rmw_fastrtps_cpp*` default Tier 1; `rmw_zenoh_cpp` Eclipse Zenoh Tier 1, all platforms. The asterisk marks the default RMW. A rolling Lyrical release note was fetched in the survey and had no middleware-default table; no Lyrical default was invented. sha256 `bd04ae8735918259940873939480a40e1c648143598961b306432d4abfd0b5cc`.
- Wikipedia, Inverse kinematics, oldid 1380700181, https://en.wikipedia.org/w/index.php?title=Inverse_kinematics&oldid=1380700181 action=raw, HTTP 200. Body read. Jacobian inverse / Moore–Penrose pseudoinverse: `Δx ≈ J_p^+(x_0) Δp`. sha256 `eed3009c8839548574f8255b392ac14f0ba9bdacc6fbd699d858dc7ff4c4dde5`.
- Wikipedia, Moore–Penrose inverse, oldid 1382104859, https://en.wikipedia.org/w/index.php?title=Moore%E2%80%93Penrose_inverse&oldid=1382104859 action=raw, HTTP 200. Body read. Projectors section: `I - A^+A` is the orthogonal projector onto `ker(A)`; `A(I - A^+A) = 0`. sha256 `98b6b84a15d433021a11af9750d2a13e2bb8df3e9eac02e7e152e52ae220aab8`.
- Modern Robotics, Dec 2019 preprint of the updated first edition of Modern Robotics, 2017, https://hades.mech.northwestern.edu/images/2/25/MR-v2.pdf, footer “Dec 2019 preprint of updated first edition of Modern Robotics, 2017. http://modernrobotics.org”. PDF opened; sha256 `47f446567bb4ba500fced69890c4c039f8180c2a3dfd0ffdd679d9ac0a421368`. Chapter 6 Eq. 6.7: `θ̇ = J†(θ)Vd`, minimum two-norm for a redundant robot. Weighted / secondary derivation: `θ̇ = G Vd + (I-GJ) M^{-1} ∇h` subject to `Jθ̇=Vd`, with `G = M^{-1} J^T (J M^{-1} J^T)^{-1}`. The unweighted specialization `θ̇ = J^{+}v + (I-J^{+}J)z` with `G=J^{+}` is labelled as that specialization plus the Moore–Penrose projector identity, not as a verbatim MR equation. MR discusses a spatial case with `n>6`; the toy is a smaller rectangular (`n>m`) model for the same projector idea and does not misquote MR as requiring `n>6` for the planar example. Siciliano and other unopened textbooks are not cited. Already a resource on kinematics-ik.

Resource cards: ros2-zenoh-kilted, ros2-zenoh-jazzy, ros2-vendors-kilted, ros2-vendors-jazzy, ros2-kilted-release, wiki-inverse-kinematics, wiki-moore-penrose; modern-robotics was already listed. Real rmw / rmw_zenohd / ros2 run / MoveIt / TRAC-IK / real arm: 本页未运行. ROS figures 以文档为准; Wikipedia and MR figures 以原文为准.

## Declared headers and first-run results

Official first run: 2026-11-19 20:21:23 Asia/Shanghai. Official expected sha256:

- `examples/month-4/expected/rmw_zenoh_qos_discovery_toy.txt` `c6f76c9811d5b6698dfc0125042cae77ca589f5ee0c57f2fa36fe46470329c57`
- `examples/month-5/expected/redundant_ik_nullspace_toy.txt` `5da6feccbb2fc371d3970a71062570d36bed7849d176b89d54b5146e083ebacc`

Both files were rerun twice and `cmp` was byte-identical.

Common random numbers: the rmw toy shares the payload and drop sequence across arms at each regime and seed (five seeds). The IK toy shares the tip-measurement noise sequence across arms at each regime and seed (five seeds).

rmw_zenoh declared stand-in: N_PUB=40, P_DROP=0.0500, SMALL_FRAC=0.2000; reliable publisher + best-effort subscriber is incompatible under A only. Hand calc (printed): 40.0000, 38.0000, 0.2000. compatible_qos: B−A received `0.0000+-0.0000`, tie: identical on every seed — held (declared as may near-tie, including an exact tie). incompatible_qos: B−A received `38.0000+-1.0000`, clear, 5/5 — held; A received 0.0000. no_router: C−B received `-38.4000+-1.3416`, clear, 5/5 — held; C received 0.0000.

redundant IK declared 4R planar arm: LINKS 0.1000 m, reach_max 0.4000 m, DT 0.0200 s, N_STEP 80, horizon 1.6000 s, KP 4.0000 /s, KS 2.0000 /s, SIG_TIP 0.0002 m, Q_PREF 0.6000,0.7000,0.5000,0.4000 rad. mid_workspace: declared A/B primary near-tie **did not hold**; B−A primary_mm `-2.175e-6+-2.755e-7`, small but consistent, 5/5, kept (about four to five orders of magnitude smaller than the 0.0793 mm primary error, hand calc). C−A primary 11.9447+-0.0078, clear, 5/5. near_joint_limit: B−A primary `-0.0016+-0.0031`, near-tie — held as comparable primary error; B−A secondary_cost `-0.7757+-4.637e-5`, clear, 5/5 — held; C−A primary 42.6440+-0.0731, clear, 5/5 — held. Stretched configuration printed rank=1, det(JJt)=0.0000; no secondary-task win declared.

## Declared expectations that did not hold

mid_workspace A/B primary near-tie did not hold as a near-tie. The printed small but consistent gap `-2.175e-6+-2.755e-7` mm (5/5) is kept and disclosed in the en/zh results, not only in the alternatives sentence. No retune.

## Post-hoc choices

None of the official parameters were changed after the first official run. Named alternatives on the same seeds, not adopted:

- rmw toy: `P_DROP=0.2000` (hand_calc expected received if discovered = 32.0000); compatible B−A remains an exact tie (32.4000+-2.5100); incompatible B−A remains a clear gap (33.6000+-1.1402). Swapped best-effort publisher / reliable subscriber is compatible under the stand-in rule, so A and B tie at 38.0000+-1.0000 received.
- IK toy: `KS=0.5000`; mid-workspace B−A primary remains a small consistent gap (-1.147e-6+-1.261e-7); near a joint limit primary remains a near-tie (-0.0007+-0.0033) and secondary cost is still a clear B improvement (-0.5939+-4.412e-5); C still loses on primary error (15.2432+-0.0797 mm).

## Typography notes

Official expected/ uses ASCII minus and `+-` in printed toy numbers, generated with ROUND_HALF_UP. Lesson prose quotes those official strings with the same ASCII minus / `+-` typography. No typography or layout rewrite of official numbers after the first run. After that official run, lesson typography was adjusted so Chinese bold spans do not contain or sit against a full-width colon, the English ros2-setup body includes the exact wording “not listed on the Jazzy vendors packaged table,” each new Summary sentence includes 本页未运行, the ros2-setup run block names `examples/month-4/ros2-setup` in prose before `python3`, and paired labels in the new kinematics section use official ASCII `B-A` typography rather than a Unicode minus. Those adjustments are disclosed in the en/zh results paragraphs. A later wording-only fix, with expected/ untouched, corrected the mid-workspace orders-of-magnitude comparison in the en/zh results and in this note: 0.0793 / 2.175e-6 is about four to five orders of magnitude (hand calc), not six. The same fix labelled the exercise-1 remaining lengths 0.4000, 0.3000, 0.2000, 0.1000 m as hand calc, because that length tuple is not printed in expected/ (0.2000 appears only as SMALL_FRAC). Curriculum objective text uses the site's usual unicode minus on a few paired figures; that is curriculum metadata, not a change to expected/.

## Code changes after the first run

No official toy or expected/ change after the first run. The official expected/ files were frozen at 20:21:23 Asia/Shanghai and remained byte-identical on rerun. Lesson prose, plans, locks and tests were written from that output afterwards. Subsequent lesson typography adjustments (Chinese bold punctuation, the exact Jazzy packaged-table wording, and 本页未运行 in the new Summary sentences) are disclosed in the en/zh results and in the typography notes above; official numbers were not rewritten. The later wording-only fix to the mid-workspace orders-of-magnitude comparison and the exercise-1 hand-calc length labels is also disclosed there; expected/ was not changed.

## Mismatch with §9

The mid_workspace primary cell was declared as a possible near-tie and came back as a small but consistent gap; it is kept, not retuned, and disclosed in en/zh results. Other pre-declared cells held (compatible QoS as an exact tie, which is allowed by the “may near-tie” wording; incompatible QoS and no-router losses; near-limit secondary win at comparable primary error; unprojected primary loss).

## Lock changes

New batch-25 PR1 block in `tools/check_diagrams.mjs` (toys, expected, CRN, label order, rectangular `n>m`, Zenoh not default / not Jazzy Tier 1, existing discovery-env sentence still present, unweighted specialization wording, sources, plans, README, declared regimes, mid-workspace disclosure) plus `tools/test_b25p1_rmw_zenoh_ik_toys.py`. Tipped site-total, host-minute, month-total and Current-header locks only (42300→42660, M4 3570→3750, M5 3750→3930, ros2-setup 360→540, kinematics-ik 750→930). Historical strings inside already-written plan/sources files (including month-11-plan `41940→42300`) were not edited. No lock relaxed. `kinematics.py` is untouched. The existing English sentence “Both are read by the default DDS layers; the newer Zenoh RMW supports neither.” and the Chinese “两者都由默认的 DDS 层读取；较新的 Zenoh RMW 两个都不支持。” are unchanged.

- README `/42 300/` and `约 42 300 分钟` → `/42 660/` and `约 42 660 分钟`.
- Curriculum sum checks `42300` → `42660`; live M4/M5 sum checks 3570→3750 and 3750→3930; live host-minute checks 360→540 on ros2-setup and 750→930 on kinematics-ik.
