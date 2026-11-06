#!/usr/bin/env python3
"""Independent mode-table, split-edge, counter and CRC oracle regressions."""
import ast
from collections import Counter
from pathlib import Path
import runpy
import zlib

ROOT=Path(__file__).resolve().parents[1]
paths=('examples/month-2/sensors-fusion/spi_mode_mismatch_toy.py',
       'examples/month-2/timing-interrupts/hw_wdt_kick_toy.py',
       'examples/month-8/dataset-engineering/dataset_crc_integrity_toy.py')
for path in paths:
    for node in ast.walk(ast.parse((ROOT/path).read_text())):
        if isinstance(node,ast.Import):assert all(x.name=='zlib' for x in node.names)
        if isinstance(node,ast.ImportFrom):assert node.module=='bisect'
s,w,c=(runpy.run_path(str(ROOT/path)) for path in paths)
assert [s['sample_rising'](mode) for mode in range(4)]==[True,False,False,True]
# Exhaustive data patterns: matched sampling, BOTH bit orders and both apertures.
for value in range(256):
    payload=bytes((value,))
    for mode in range(4):
        for order in s['ORDERS']:
            wire=s['waveform'](payload,mode,order)
            for aperture in s['APERTURES']:
                assert s['receive'](wire,mode,order,aperture)==payload
wire=s['waveform'](bytes((0xA5,)),0,'MSB')
assert s['receive'](wire,1,'MSB',.3)==bytes((0x4A,))
assert s['receive'](wire,1,'MSB',.1)==bytes((0xA5,)) # A mismatch can pass!
wire=s['waveform'](bytes((0xA5,)),1,'MSB')
assert s['receive'](wire,0,'MSB',.1)==bytes((0x52,))
for mode in range(4):
    for order in s['ORDERS']:
        wire=s['waveform'](s['PAYLOAD'],mode,order)
        for aperture in s['APERTURES']:
            assert s['receive'](wire,mode^1,order,aperture)==s['receive'](wire,mode^2,order,aperture)
# Receiver samples waveform voltage, not the expected payload or a canned shift.
edges=tuple((float(j),j%2==1,True) for j in range(1,17))
changes=((-1.,1),) # Physical wire constant high at all selected sample points.
assert s['receive']((edges,changes),0,'MSB',.1)==b'\xff'
assert s['receive']((tuple((t,r,False) for t,r,_ in edges),changes),0,'MSB',.1)==b''
try:s['receive']((edges[1:],changes),0,'MSB',.1)
except ValueError:pass
else:raise AssertionError('partial CS frame not rejected')
assert s['receive'](s['waveform'](b'\x96',0,'MSB'),0,'LSB',.1)==b'\x69'
# Independent watchdog deadline from the last completed main-loop kick at25.
assert w['run']('no_kick')['reset_at']==16
assert w['run']('main_loop')['reset_at'] is None
main=w['run']('main_loop',30);isr=w['run']('isr_timer',30)
assert main['reset_at']==25+w['TIMEOUT']==41 and main['saved_mcusr']==8 and main['cleared_mcusr']==0
assert main['progress']==isr['progress']==29 and isr['reset_at'] is None and isr['hidden']
assert w['run']('main_loop',1)['reset_at']==16
assert w['run']('main_loop',kick_period=16)['reset_at']==16 # Deadline tie too late.
assert w['run']('main_loop',kick_period=5,window_min=8)['reason']=='window_early'
assert w['run']('main_loop',kick_period=8,window_min=8)['reset_at'] is None
assert w['run']('main_loop',30,10,8)['reset_at']==36
assert w['PRESCALE']==((0,2048,16),(1,4096,32),(2,8192,64),(3,16384,125),(4,32768,250),(5,65536,500),(6,131072,1000),(7,262144,2000),(8,524288,4000),(9,1048576,8000))
# Native stdlib oracle, independent of the bitwise implementation.
assert c['POLY']==0xEDB88320 and c['crc32'](b'123456789')==0xCBF43926
assert c['crc32'](b'')==0
corpus=c['corpus']();counts=Counter(kind for kind,_,_ in corpus)
assert counts=={'single_bit':512,'burst_2to32':13888,'balanced_bytes':32,'generator_33':4}
miss=Counter()
for kind,original,received in corpus:
    assert original!=received
    tags=(c['sum8'](original),zlib.crc32(original)&0xFFFFFFFF)
    assert c['crc32'](received)==zlib.crc32(received)&0xFFFFFFFF
    for arm in ('no_check','sum8','CRC32'):
        miss[(kind,arm)]+=c['accepted'](arm,received,tags)
assert all(miss[(kind,'no_check')]==count for kind,count in counts.items())
assert all(miss[(kind,'CRC32')]==0 for kind in ('single_bit','burst_2to32','balanced_bytes'))
assert miss[('burst_2to32','sum8')]==116 and miss[('balanced_bytes','sum8')]==32
assert miss[('generator_33','CRC32')]==4 and miss[('generator_33','sum8')]==0
# Arbitrary interior patterns, not only runs of ones, and boundary-crossing bursts.
for length in range(1,33):
    for start in (0,7,128-length):
        for interior in (0,0x12345678,0xAAAAAAAA):
            mask=1 if length==1 else 1|(1<<(length-1))|((interior & ((1<<(length-2))-1))<<1)
            changed=c['flip'](c['PAYLOADS'][2],start,mask)
            assert c['crc32'](changed)!=c['crc32'](c['PAYLOADS'][2])
for payload in c['PAYLOADS']:
    assert all(c['accepted'](arm,payload,(c['sum8'](payload),c['crc32'](payload))) for arm in ('no_check','sum8','CRC32'))
print('independent four-mode exhaustive bytes, delayed wire capture, CS framing, hidden hang/window deadlines, CRC oracle/bursts/collisions and shared corpus passed')
