#!/usr/bin/env python3
"""Deterministic synthetic logged chunks, NOT a change to LeRobot/Parquet format.
Same original payload/tags and exact corrupted cases for no-check, sum8, CRC32.
CRC-32/IEEE (ISO-HDLC): reflected 0xEDB88320, init/xorout 0xFFFFFFFF.
Payload-only errors; stored tags/length/framing intact in this experiment.
CRC is error detection, NOT authentication: collisions exist and tags can be forged.
"""
import zlib

POLY=0xEDB88320
PAYLOADS=(bytes(16),bytes([255])*16,bytes(range(16)),bytes((37*j+11)%256 for j in range(16)))


def crc32(data):
    state=0xFFFFFFFF
    for byte in data:
        state^=byte
        for _ in range(8):
            state=(state>>1)^(POLY if state&1 else 0)
    return state^0xFFFFFFFF


def sum8(data):
    return sum(data)&0xFF


def flip(data, start, mask):
    result=bytearray(data)
    for j in range(mask.bit_length()):
        if mask>>j&1:
            bit=start+j
            result[bit//8]^=1<<(bit%8)  # Contiguous on the reflected, LSB-first bit stream.
    return bytes(result)


def corpus():
    """All locations; 1-bit errors and all-ones bursts are samples, not all shapes."""
    rows=[]
    for original in PAYLOADS:
        for start in range(128):
            rows.append(("single_bit",original,flip(original,start,1)))
        for length in range(2,33):
            for start in range(129-length):
                rows.append(("burst_2to32",original,flip(original,start,(1<<length)-1)))
        for j in range(0,16,2):
            changed=bytearray(original)
            changed[j]=(changed[j]+1)&255
            changed[j+1]=(changed[j+1]-1)&255
            rows.append(("balanced_bytes",original,bytes(changed)))
        # Full reversed generator spans33 bits: an explicit long-burst collision.
        rows.append(("generator_33",original,flip(original,0,(POLY<<1)|1)))
    return tuple(rows)


def accepted(arm, received, tags):
    if arm=="no_check":
        return True
    if arm=="sum8":
        return sum8(received)==tags[0]
    if arm=="CRC32":
        return crc32(received)==tags[1]
    raise ValueError("unknown integrity arm")


def main():
    assert crc32(b"123456789")==0xCBF43926
    print(f'CRC32_IEEE("123456789")=0x{crc32(b"123456789"):08X}; reflected_poly=0x{POLY:08X}')
    print("init=xorout=0xFFFFFFFF; same4 synthetic16-byte chunks; tags/framing uncorrupted")
    print("group arm corrupted undetected undetected_rate")
    rows=corpus()
    for group in ("single_bit","burst_2to32","balanced_bytes","generator_33"):
        cases=tuple((original,received) for kind,original,received in rows if kind==group)
        for arm in ("no_check","sum8","CRC32"):
            misses=0
            for original,received in cases:
                assert received!=original
                assert crc32(received)==zlib.crc32(received)&0xFFFFFFFF
                misses+=accepted(arm,received,(sum8(original),crc32(original)))
            print(f"{group} {arm} {len(cases)} {misses} {misses/len(cases):.6f}")
    clean=[sum(accepted(arm,p,(sum8(p),crc32(p))) for p in PAYLOADS) for arm in ("no_check","sum8","CRC32")]
    print(f"clean acceptance: no_check={clean[0]}/4 sum8={clean[1]}/4 CRC32={clean[2]}/4")
    original=PAYLOADS[2];tampered=flip(original,0,1)
    forged=(sum8(tampered),crc32(tampered))
    print(f"attacker_recomputed_tags: sum8_accept={int(accepted('sum8',tampered,forged))} CRC32_accept={int(accepted('CRC32',tampered,forged))}")
    print("CRC detects ANY single nonzero burst span<=32 bits by polynomial degree, not by this finite enumeration")
    print("33-bit collision is deliberate; CRC != authentication; no random/channel-probability claim")
    print("Real recording/storage faults and format integration: 本页未运行")


if __name__=="__main__":
    main()
