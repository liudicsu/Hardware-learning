#!/usr/bin/env python3
"""Classic CAN event-level confinement; Bosch CAN 2.0 Part A pp.24-26.
Opened primary spec: https://www.canlab.cz/sites/default/files/pages/download/Can2spec.pdf
Inputs are QUALIFIED rule events, not a bit/CRC/arbitration/ACK decoder.
Normal tx_error is not the passive-ACK or arbitration-stuff exception.
REC>127 on successful receive is reset to 127 (one permitted 119..127 choice).
Recovery counts non-overlapping 11-recessive groups, then needs a toy request;
controller enable/reset policy and real SocketCAN/transceiver are not run here.
Not CiA402 status bits, EtherCAT, an e-stop or a safety certification.
"""
from dataclasses import dataclass

EVENTS = {"tx_error", "tx_ok", "tx_flag_bit", "tx_extension",
          "tx_passive_ack_exception", "tx_arbitration_stuff_exception",
          "rx_error", "rx_ok", "rx_after_flag_dominant", "rx_flag_bit", "rx_extension"}


def extension_events(flag, consecutive):
    """Rule 6 qualification only: 14th for active/overload, 8th after passive.
    Additional increments follow each further eight dominant bits. Caller must
    supply the correctly scoped sequence; this is not a wire-level parser.
    """
    if flag not in ("active", "overload", "passive") or consecutive < 0:
        raise ValueError("invalid qualified dominant sequence")
    first = 8 if flag == "passive" else 14
    return max(0, 1 + (consecutive - first) // 8)


@dataclass
class Node:
    tec: int = 0
    rec: int = 0
    accepted: int = 0
    blocked: int = 0
    recessive_run: int = 0
    sequences: int = 0
    off: bool = False

    def __post_init__(self):
        if self.tec < 0 or self.rec < 0:
            raise ValueError("negative counter")
        self.off = self.off or self.tec > 255

    @property
    def state(self):
        if self.off:
            return "bus-off"
        return "error-passive" if max(self.tec, self.rec) > 127 else "error-active"

    def apply(self, event):
        if event not in EVENTS:
            raise ValueError("unknown qualified event")
        if self.off:
            self.blocked += 1  # No TX/ACK/error flag is issued while off.
            return False
        if event in ("tx_error", "tx_flag_bit", "tx_extension"):
            self.tec += 8
        elif event == "tx_ok":
            self.tec = max(0, self.tec - 1)
            self.accepted += 1
        elif event == "tx_passive_ack_exception":
            if self.state != "error-passive":
                raise ValueError("requires passive, no dominant ACK or passive-flag bit")
        elif event == "tx_arbitration_stuff_exception":
            pass  # Qualified recessive-stuff/dominant-detected arbitration exception.
        elif event == "rx_error":
            self.rec += 1
        elif event in ("rx_after_flag_dominant", "rx_flag_bit", "rx_extension"):
            self.rec += 8
        elif event == "rx_ok":
            self.rec = 127 if self.rec > 127 else max(0, self.rec - 1)
            self.accepted += 1
        self.off = self.tec > 255
        return True

    def observe(self, bits):
        """1=recessive, 0=dominant; interrupted runs cannot form an 11-bit group."""
        if any(bit not in "01" for bit in bits):
            raise ValueError("bits must be 0/1")
        if not self.off:
            return
        for bit in bits:
            self.recessive_run = self.recessive_run + 1 if bit == "1" else 0
            if self.recessive_run == 11:
                self.sequences = min(128, self.sequences + 1)
                self.recessive_run = 0

    def request_recovery(self):
        if not self.off or self.sequences < 128:
            return False
        self.tec = self.rec = self.recessive_run = self.sequences = 0
        self.off = False
        return True


def shared_schedule():
    return (True,) * 16 + (False,) * 8 + (True,) * 17 + (False,) * 2


def transmitter_trace(noisy):
    node, checkpoints = Node(), []
    for slot, injected in enumerate(shared_schedule(), 1):
        node.apply("tx_error" if noisy and injected else "tx_ok")
        if slot in (16, 24, 40, 41, 43):
            checkpoints.append((slot, node.tec, node.rec, node.state))
    return node, checkpoints


def main():
    print("Classic CAN qualified events; shared 43 slots, deterministic, no stochastic seeds")
    print("normal TX +8/-1; REC +1/-1 plus qualified +8; passive >127; bus-off TEC>255")
    print("arm slot TEC REC state")
    for name, noisy in (("healthy", False), ("noisy_tx", True)):
        node, trace = transmitter_trace(noisy)
        for row in trace:
            print(name, *row)
        print(f"{name} accepted={node.accepted} blocked_while_off={node.blocked}")
    print("boundary TEC REC state")
    for tec, rec in ((127, 127), (128, 0), (255, 0), (256, 0), (0, 512)):
        print("boundary", tec, rec, Node(tec, rec).state)
    print("receive event before_REC after_REC")
    for event, rec in (("rx_error", 0), ("rx_ok", 1), ("rx_ok", 0),
                       ("rx_after_flag_dominant", 120), ("rx_flag_bit", 120),
                       ("rx_extension", 120), ("rx_ok", 128)):
        node = Node(rec=rec)
        node.apply(event)
        print("receive", event, rec, node.rec)
    print("rule6 flag count increments_of_8")
    for flag, count in (("active", 13), ("active", 14), ("active", 22),
                        ("overload", 14), ("passive", 7), ("passive", 8), ("passive", 16)):
        print("rule6", flag, count, extension_events(flag, count))
    node = Node(tec=128)
    node.apply("tx_passive_ack_exception")
    print(f"passive_ACK_exception TEC={node.tec}; alone-node ACK loss is not forced bus-off")
    node.apply("tx_arbitration_stuff_exception")
    print(f"arbitration_stuff_exception TEC={node.tec}")
    node = Node(tec=256)
    print(f"no_wait recovered={int(node.request_recovery())} state={node.state}")
    node.observe(("1" * 10 + "0") * 128)
    print(f"interrupted_10R_1D sequences={node.sequences} recovered={int(node.request_recovery())}")
    node.observe("1" * (127 * 11 + 10))
    print(f"1407R sequences={node.sequences} partial={node.recessive_run} recovered={int(node.request_recovery())}")
    node.observe("1")
    ready = node.sequences
    recovered = node.request_recovery()
    print(f"1408R sequences_before_reset={ready} recovered={int(recovered)} TEC={node.tec} REC={node.rec} state={node.state}")
    print("REC>127 receive-success chooses 127 from allowed 119..127; no universal register implementation")
    print("Not CiA402 status bits / EtherCAT / e-stop; real CAN + SocketCAN: 本页未运行; 以规范为准")


if __name__ == "__main__":
    main()
