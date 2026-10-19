"""sts_packet.py: build and check Feetech STS3215 bus-servo packets by hand.

The SO-101 arm's six STS3215 servos share one serial wire (half duplex, 1 Mbit/s in LeRobot).
Every message is a packet:
    0xFF 0xFF  ID  LENGTH  INSTRUCTION  PARAMS...  CHECKSUM
LENGTH = number of params + 2, CHECKSUM = ~(ID + LENGTH + INSTRUCTION + PARAMS) & 0xFF.
A servo answers with  0xFF 0xFF ID LENGTH ERROR PARAMS... CHECKSUM.
Two-byte values are little-endian (low byte first). Register addresses are from the STS
control table used by LeRobot: Torque_Enable 40, Goal_Position 42, Present_Position 56.
No hardware needed: this only prints bytes.
"""
PING, READ, WRITE = 0x01, 0x02, 0x03
TORQUE_ENABLE, GOAL_POSITION, PRESENT_POSITION = 40, 42, 56
STEPS_PER_TURN = 4096                       # 12-bit magnetic encoder


def checksum(body):
    return ~sum(body) & 0xFF


def packet(servo_id, instruction, params=()):
    body = [servo_id, len(params) + 2, instruction, *params]
    return bytes([0xFF, 0xFF, *body, checksum(body)])


def hexs(data):
    return " ".join(f"{b:02X}" for b in data)


def parse_status(data):
    """Check a reply and return (id, error byte, params)."""
    if data[:2] != b"\xff\xff":
        raise ValueError("no 0xFF 0xFF header")
    servo_id, length, error = data[2], data[3], data[4]
    params = data[5:5 + length - 2]
    if checksum(data[2:5 + length - 2]) != data[5 + length - 2]:
        raise ValueError("bad checksum: the bytes were corrupted on the wire")
    return servo_id, error, params


if __name__ == "__main__":
    goal = 2048                                     # half a turn = the middle of the range
    print(f"{'ping servo 1:':32s}", hexs(packet(1, PING)))
    print(f"{'torque on, servo 1:':32s}", hexs(packet(1, WRITE, [TORQUE_ENABLE, 1])))
    print(f"{'goal position 2048, servo 1:':32s}", hexs(packet(1, WRITE, [GOAL_POSITION, goal & 0xFF, goal >> 8])))
    print(f"{'read present position, servo 6:':32s}", hexs(packet(6, READ, [PRESENT_POSITION, 2])))

    reply = bytes([0xFF, 0xFF, 0x06, 0x04, 0x00, 0x2C, 0x0C])   # a made-up answer from servo 6
    reply += bytes([checksum(reply[2:])])
    sid, err, params = parse_status(reply)
    steps = params[0] | params[1] << 8
    print(f"reply {hexs(reply)} -> servo {sid}, error {err}, position {steps} "
          f"= {steps * 360 / STEPS_PER_TURN:.1f} deg")
    broken = reply[:-2] + bytes([reply[-2] ^ 0x01]) + reply[-1:]  # flip one bit on the wire
    try:
        parse_status(broken)
    except ValueError as e:
        print(f"reply {hexs(broken)} -> {e}")
