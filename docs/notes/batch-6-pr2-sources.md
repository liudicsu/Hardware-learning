# Batch-6 PR2 sources / 来源核对

Downloaded with `curl -fL`, HTTP **200** for all used URLs; PDF bodies opened via `pdftotext -layout`, HTML article bodies read. Audit: 2026-11-06 10:30 CST, Asia/Shanghai (UTC+8).

| Opened source | URL | GET | SHA-256 of downloaded body |
|---|---|---|---|
| Bosch CAN 2.0, September 1991 (public mirror) | [https://www.canlab.cz/sites/default/files/pages/download/Can2spec.pdf](https://www.canlab.cz/sites/default/files/pages/download/Can2spec.pdf) | 200 | `0966662d9b0419e62b2d08edf701c63b9e6a305e157ada3c489e62dd03621da8` |
| NXP BCANPSV2.0 Rev.3 | [https://www.nxp.com/docs/en/reference-manual/BCANPSV2.pdf](https://www.nxp.com/docs/en/reference-manual/BCANPSV2.pdf) | 200 | `4cdadf8a70719f30b9c4bb34866424593d5b123e3c1cb27ad4015f0a5031975f` |
| ft_tools_ros2 rendered calibration README | [https://github.com/tpoignonec/ft_tools_ros2](https://github.com/tpoignonec/ft_tools_ros2) | 200 | `5b63946e0367aa4654396b559749a2bba8104c55508958a9dcd1c389cf748908` |
| Jazzy admittance userdoc | [https://control.ros.org/jazzy/doc/ros2_controllers/admittance_controller/doc/userdoc.html](https://control.ros.org/jazzy/doc/ros2_controllers/admittance_controller/doc/userdoc.html) | 200 | `827f58f7ce360b335106f42d1ee20d38a8c64a983085f29e6c86644d44c9a54c` |

- **Bosch Part A pp.24–26:** all twelve confinement rules were opened: ordinary REC+1 exclusions, post-flag dominant +8, flag-bit +8, normal TEC+8 with both no-increment exceptions, rule6 first 14th/8th then each additional8, success floors and REC>127 reset119…127, passive≥128, bus-off TEC≥256, recovery128 occurrences of11 recessive bits. Toy chooses127 after high-REC success and accepts prequalified events, not a full decoder. Controller recovery policy and actual SocketCAN are not reproduced. / 不杜撰完整协议或硬件行为。
- **NXP §5.2:** independently corroborates thresholds, ordinary counter changes and recovery. Its historical rule6 wording is not identical to Bosch's original; do not merge the two. Use Bosch for that detail. Official Bosch-hosted can2spec.pdf URL returned HTTP404; that body was not used. The named public mirror was opened successfully instead. / 主来源镜像可读，失败链接不冒认。
- **ft_tools_ros2 README FT calibration/estimation:** sensor-frame mass/COM/offset LS, approximately ten well-chosen poses, own EigenSVD solver, and rotated/translated wrench formulas actually read. Our six full-rank synthetic orientations and QR are not its implementation. README uses reaction −mg; toy explicitly defines payload-on-sensor +mg. All compensation parameters are estimated from calibration only. / 真值仅生成与评分，不给拟合器。
- **Jazzy userdoc:** fixed-world frame, gravity-compensation frame, CoG.pos and CoG.force=mass×9.81 opened; no controller or hardware run. / 不冒认实测。

## Task precedence and accounting / 指令与核算

The latest user explicitly relocates H2 to **8.4** and requires bus-off **TEC>255**, overriding the older proposal §9's **8.5 / reaches255** wording. Keep 8.5 content unchanged; CAN diagnostics are separate from CiA402, EtherCAT and e-stop. H5 stays9.3. **21570+180+210=21960**, M8 **2670→2850**, M9 **2730→2940**,71 lessons; M1/M2 stay1020/1980. No PR3 minutes or workflow edits.

## Tool attempts / 工具尝试

Free opencode attempted in order DeepSeek v4.1 Flash, GLM5.3 Flash, MiMo v2.6 Flash with a self-contained no-tool calibration-audit request; each timed out at70s without a completed answer. LongCat/MiniMax free IDs absent from installed catalog. Implemented locally; no paid model or permission-policy changes.
