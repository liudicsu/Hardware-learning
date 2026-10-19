"""compare_sdk.py: check sts_packet.py against Feetech's own Python SDK, no servo needed.

The SDK writes its packets to a fake serial port that just records the bytes.
Needs:  pip install feetech-servo-sdk   (tested with 1.0.0; it also installs pyserial)
"""
import scservo_sdk as scs

import sts_packet as mine


class FakePort:
    """Just enough of scservo_sdk.PortHandler for the SDK to send a packet."""
    is_using = False
    baudrate = 1_000_000

    def __init__(self):
        self.sent = b""

    def clearPort(self):
        pass

    def setPacketTimeout(self, length):
        pass

    def writePort(self, packet):
        self.sent = bytes(packet)
        return len(packet)


def sent_by_sdk(call):
    port = FakePort()
    call(scs.PacketHandler(0), port)          # 0 = STS byte order (little-endian)
    return port.sent


cases = [
    ("ping 1", lambda h, p: h.txPacket(p, [0, 0, 1, 2, scs.INST_PING, 0]), mine.packet(1, mine.PING)),
    ("torque on 1", lambda h, p: h.write1ByteTxOnly(p, 1, 40, 1), mine.packet(1, mine.WRITE, [40, 1])),
    ("goal 2048 on 1", lambda h, p: h.write2ByteTxOnly(p, 1, 42, 2048), mine.packet(1, mine.WRITE, [42, 0x00, 0x08])),
    ("read position 6", lambda h, p: h.readTx(p, 6, 56, 2), mine.packet(6, mine.READ, [56, 2])),
]
for name, call, expected in cases:
    got = sent_by_sdk(call)
    print(f"{name:16s} SDK {mine.hexs(got):27s} {'same' if got == expected else 'DIFFERENT'}")
