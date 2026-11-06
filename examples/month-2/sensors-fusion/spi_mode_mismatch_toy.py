#!/usr/bin/env python3
"""Deterministic SPI edge surrogate; no device clock rate or analog validation.
Shared physical MOSI/SCK/CS per TX mode/order and aperture case for all RX arms.
Synthetic time units: half period=1, propagation=0.2, apertures=0.1/0.3.
Wrong-edge capture coincides with launch; which bit arrives is timing-dependent,
not a prediction of real metastability. Both clean mismatches and shifted garbage
are intentional. Eight-bit words in one active-low CS frame; COPI/MOSI only.
"""
from bisect import bisect_right

PAYLOAD = bytes((0xA5,0x00,0xFF,0x3C,0x81,0x01,0x96,0x69))
DELAY = .2
APERTURES = (.1,.3)
ORDERS = ("MSB","LSB")


def bits_of(data, order):
    positions=range(7,-1,-1) if order=="MSB" else range(8)
    return tuple((byte>>bit)&1 for byte in data for bit in positions)


def sample_rising(mode):
    cpol,cpha=divmod(mode,2)
    return (cpol==0) == (cpha==0)


def waveform(data, mode, order):
    cpol,cpha=divmod(mode,2)
    bits=bits_of(data,order)
    # Unselected clocks before/after the CS frame must not enter RX framing.
    edges=[(-2.,True,False),(-1.,False,False)]
    changes=[(-10.,0)]
    if cpha==0:
        changes.append((0.,bits[0]))  # First bit preloaded before leading edge at t=1.
    for j,bit in enumerate(bits):
        lead,trail=2*j+1.,2*j+2.
        edges.extend(((lead,cpol==0,True),(trail,cpol==1,True)))
        launch=lead if cpha else trail
        value=bit if cpha else (bits[j+1] if j+1<len(bits) else 0)
        changes.append((launch+DELAY,value))
    edges.extend(((2*len(bits)+1.,True,False),(2*len(bits)+2.,False,False)))
    return tuple(edges),tuple(changes)


def receive(wire, mode, order, aperture):
    edges,changes=wire
    times=tuple(t for t,_ in changes)
    captured=[]
    for time,rising,selected in edges:
        if selected and rising==sample_rising(mode):
            index=bisect_right(times,time+aperture)-1
            captured.append(changes[index][1])
    if len(captured)%8:
        raise ValueError("partial 8-bit CS frame")
    positions=range(7,-1,-1) if order=="MSB" else range(8)
    return bytes(sum(bit<<place for bit,place in zip(captured[j:j+8],positions))
                 for j in range(0,len(captured),8))


def bit_errors(expected, actual):
    if len(expected)!=len(actual):
        raise ValueError("framing length differs")
    return sum((a^b).bit_count() for a,b in zip(expected,actual))


def main():
    print("SPI synthetic edge schedule: half_period=1 prop_delay=0.2 aperture=0.1/0.3 time units")
    print("shared payload=A5 00 FF 3C 81 01 96 69; 64 bits; one active-low CS frame")
    print("TX_mode order aperture RX_arm RX_mode errors BER first_byte")
    for mode in range(4):
        for order in ORDERS:
            wire=waveform(PAYLOAD,mode,order)
            for aperture in APERTURES:
                for name,rx in (("matched",mode),("CPOL_wrong",mode^2),("CPHA_wrong",mode^1)):
                    result=receive(wire,rx,order,aperture)
                    errors=bit_errors(PAYLOAD,result)
                    print(f"{mode} {order} {aperture:.1f} {name} {rx} {errors} {errors/64:.6f} {result[0]:02X}")
    print("varied-pattern diagnostic: TX1 MSB aperture0.1 RX0 (wrong phase)")
    result=receive(waveform(PAYLOAD,1,"MSB"),0,"MSB",.1)
    print(" ".join(f"{a:02X}->{b:02X}" for a,b in zip(PAYLOAD,result)))
    print("isolated-byte same wrong mode/timing: "+" ".join(
        f"{v:02X}->{receive(waveform(bytes((v,)),1,'MSB'),0,'MSB',.1)[0]:02X}"
        for v in (0x00,0xFF,0xA5,0x96)))
    reversed_order=receive(waveform(bytes((0x96,)),0,"MSB"),0,"LSB",.1)
    print(f"wrong bit order: TX96 MSB decoded_LSB={reversed_order[0]:02X}")
    print("CS-high clocks ignored; partial 8-bit CS frames rejected; CS is not a device address")
    print("Wrong-edge zero BER is possible in this timing model, NOT proof of a compatible mode")
    print("No noise/no random seeds; no MHz claim; real device/scope: 本页未运行")


if __name__=="__main__":
    main()
