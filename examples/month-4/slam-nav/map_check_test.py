#!/usr/bin/env python3
"""Negative tests for map_check.py: it must reject maps that are wrong, not only pass good ones.

usage: python3 map_check_test.py [map.yaml]     (default: test/room.yaml, a map saved by a real run)
1. the map as saved must pass (exit code 0);
2. a blank map (every cell unknown, and every cell free) must fail;
3. the map with one object erased (its footprint plus one cell all round set to free) must
   fail, once for each object in map_check.OBJECTS.
Prints one line per case and the FAIL lines map_check printed; exit code 1 if any case is wrong.
tools/sim/ros/run.sh runs this on every freshly saved map. Standard library only."""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import map_check  # noqa: E402


def write_map(folder, name, width, height, rows, res, origin):
    with open(os.path.join(folder, name + '.pgm'), 'wb') as f:
        f.write(b'P5\n%d %d\n255\n' % (width, height) + b''.join(bytes(r) for r in rows))
    with open(os.path.join(folder, name + '.yaml'), 'w') as f:
        f.write(f'image: {name}.pgm\nmode: trinary\nresolution: {res}\n'
                f'origin: [{origin[0]}, {origin[1]}, {origin[2] if len(origin) > 2 else 0}]\n'
                'negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n')
    return os.path.join(folder, name + '.yaml')


def erase(rows, width, height, res, origin, obj):
    """Set the cells map_check looks at for one object to free (254), as if it was not there."""
    cx, cy, hx, hy = obj
    rows = [bytearray(r) for r in rows]
    steps_x, steps_y = int(2 * (hx + res) / res) + 1, int(2 * (hy + res) / res) + 1
    for i in range(steps_x):
        for j in range(steps_y):
            col = int((cx - hx - res + i * res - origin[0]) / res)
            row = height - 1 - int((cy - hy - res + j * res - origin[1]) / res)
            if 0 <= col < width and 0 <= row < height:
                rows[row][col] = 254
    return rows


def run(yaml_path):
    p = subprocess.run([sys.executable, os.path.join(HERE, 'map_check.py'), yaml_path],
                       capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).rstrip('\n').split('\n')


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'test', 'room.yaml')
    image, res, origin = map_check.read_yaml(src)
    width, height, rows = map_check.read_pgm(os.path.join(os.path.dirname(src), image))
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        cases.append(('saved map', src, 0))
        cases.append(('blank map, all unknown',
                      write_map(tmp, 'blank_unknown', width, height, [[205] * width] * height, res, origin), 1))
        cases.append(('blank map, all free',
                      write_map(tmp, 'blank_free', width, height, [[254] * width] * height, res, origin), 1))
        for k, (name, obj) in enumerate(map_check.OBJECTS.items()):
            cases.append((f'{name} erased', write_map(tmp, f'erased{k}', width, height,
                                                       erase(rows, width, height, res, origin, obj), res, origin), 1))
        bad = 0
        for label, path, want in cases:
            code, out = run(path)
            ok = (code == 0) == (want == 0)
            bad += not ok
            verdict = 'ok  ' if ok else 'WRONG'
            print(f'{verdict} {label}: map_check exit {code} (want {"pass" if want == 0 else "fail"})')
            for line in out:                       # why map_check failed (or all of it if wrong)
                if not ok or line.startswith('FAIL'):
                    print('        ' + line)
    print(f'{len(cases)} cases, {bad} wrong')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
