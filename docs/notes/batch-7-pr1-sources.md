# Batch-7 PR1 source/model audit

2026-11-06 11:16:55 Asia/Shanghai (UTC+8). Base `6c8febf70b336a1c945811ae152fa787690580d7` (#128 merged), new `feat/spi-wdt-crc` worktree `/workspace/hl-b7p1`, node_modules hardlinked with cp -al, not symlinked. Proposal §9 read first, then H1/H2/H7 and full avoid list. No polish-worktree edits.

## Arithmetic: this PR only

22350 +180 +150 +150 = **22830**, still71 lessons. M2 1980+180+150=**2310**; M8 3030+150=**3180**. No arithmetic mismatch. Host minutes: sensors-fusion360→540, timing-interrupts180→330, dataset-engineering180→330. Other month/lesson minutes unchanged.

## Opened and curl-verified sources

| source | URL | HTTP | fetched-copy SHA256 |
|---|---|---|---|
| Arduino SPI | https://docs.arduino.cc/learn/communication/spi/ | 200 | `40fb85ee71d3899608f90181ea6e0418f432b2b92e93ea10cb77e61c8086ac2c` |
| Arduino actual content payload | https://docs.arduino.cc/page-data/learn/communication/spi/page-data.json | 200 | `5591a602eb0f9c97d2d20ac8419ff8b22f554c68d0675c5e7c7c71ef77144968` |
| ATmega328P 7810D | https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7810-Automotive-Microcontrollers-ATmega328P_Datasheet.pdf | 200 | `fb84858d0b12c695a12b13f0c74b962d81210247d440c7a24c0ed23dfabfdfaf` |
| CRC secondary reference | https://en.wikipedia.org/wiki/Cyclic_redundancy_check | 200 | `32d6a2b69b36f0eae9cadb928357158cc9ab8ad52c0ace6140a7779b076bc4ba` |

- Arduino public HTML is a JavaScript shell. Its public Gatsby page-data body was also curl200 and opened/read: SPI_MODE0/1/2/3 capture rising/falling/falling/rising, CPOL/CPHA, bit order and CS. No device MHz copied from unnamed example chips. Analog AN-1248 is not cited/used; the proposal's unresolved link is not a source claim.
- ATmega328P **7810D–AVR–01/15**, pp44–48: independent128kHz oscillator, WDR, Table10-2 WDE/WDIE/fuse modes; Table10-3 WDP3..0 codes0000..1001,2048..1048576cycles,typical16ms..8s at5V;1010..1111 reserved. MCUSR.WDRF bit3, save then clear early, WDRF override ofWDE and WDCE timed four-cycle configuration. These are this opened revision's typical readings, not real-board measurements. The toy is not full register/fuse/bootloader emulation.
- CRC Wikipedia is explicitly **secondary**: GF(2) polynomial detection, reflected IEEE polynomial, burst-span theorem and authentication limitation. CRC-32/ISO-HDLC check value0xCBF43926 independently verified with stdlib zlib, all new corrupted cases cross-checked too. No claim that LeRobotDataset v3 stores this toy checksum.

## Model fairness / limits

- **SPI:** same physical MOSI/SCK/CS per TX mode/order/capture aperture to matched, CPOL-wrong and CPHA-wrong arms. Those two wrong modes select the same opposite edge here. Synthetic half-period1/propagation0.2/capture offsets0.1 or0.3; first-bit preload, stable matched edges, wrong-edge old/new capture, MSB/LSB and active-low CS framing explicit. BER/first-byte shift; varied isolated patterns expose accidental passes. No metastability prediction, no clock MHz claim or analog validation. Independent exhaustive256-byte tests cover all modes/orders/apertures and waveform-not-answer capture.
- **HW WDT:** same tick/time/hang for all kick arms; independent counter is not software command-timeout8.5. Reset-before-kick deadline tie; stop at first reset, no reboot behavior. Main progress stops at29 afterhang30; main kicks last25→reset41, ISR kicks hide hang. Generic early window[8,16) is NOT ATmega328P hardware; no AVR flag attributed to generic early fault. The1ms ideal tick/16tick deadline approximates a chosen nominal table interval without oscillator tolerance/CPU timing. No safety certification/e-stop claim.
- **CRC:** shared four16-byte chunks, tags and corrupted corpus to no-check/sum8/CRC32; no-check ignores tags. Tags/framing remain intact; conditional undetected-error rate is over corrupted cases, not real channel probability. Single-bit exhaustive512; all-ones spans2..32 at every fitting position13888; balanced-byte32; deliberate full-generator33-bit collision4. Finite all-ones enumeration is not a proof of all burst shapes: the degree/constant-term argument is supplied separately. Longer/multiple errors and recomputed-tag adversaries can pass; CRC≠authentication. Independent zlib/oracle, sparse burst and collision tests run.
- Entirely deterministic: no random simulation/no stochastic seed claim; the ≥5-seed rule is not invoked. Real SPI/scope, AVR fuse/reset lab and real recording/storage integration are 本页未运行.

## Execution notes

Requested opencode free-model order tried starting with DeepSeek (`opencode/deepseek-v4.1-flash-free`): **successful read-only design audit** highlighted SPI capture assumptions, ISR-hidden progress loss and checksum/authentication limits; those suggestions were independently checked. Stopped at first usable model, so GLM/MiMo were not needed. LongCat/MiniMax free IDs absent from the current catalog. Implemented locally, no CloudAgent tool available. No workflow edits; no prior expected outputs overwritten. Existing optional local dependency skips (OpenSCAD/month3 SDK/month7 MuJoCo) remain unchanged and are reported with validation results.
