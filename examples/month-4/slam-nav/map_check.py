#!/usr/bin/env python3
"""Check a saved map against the world it came from: are the walls and obstacles where the
obstacles world (Lesson 4) put them?

usage: python3 map_check.py ~/maps/room.yaml      (exit code 1 if an object is missing or the map is too empty)
Reads the .yaml and .pgm written by nav2_map_server's map_saver_cli. Only the Python standard
library is needed. The map frame starts where the robot was spawned, the centre of the room."""
import os
import sys

# what is really in the obstacles world, in the map frame (centre x, centre y, half x, half y)
OBJECTS = {
    'north wall': (3.0, 0.0, 0.05, 3.0),
    'south wall': (-3.0, 0.0, 0.05, 3.0),
    'west wall': (0.0, 3.0, 3.05, 0.05),
    'east wall': (0.0, -3.0, 3.05, 0.05),
    'red box': (2.0, 0.0, 0.2, 0.2),
    'blue pillar': (1.0, -1.2, 0.15, 0.15),
    'green block': (-1.5, 1.5, 0.6, 0.6),   # 1.2 x 0.3 m turned 0.6 rad: check its bounding square
}
# The fewest occupied cells that still count as "found", and the fewest occupied and free cells
# in the whole map: about half the smaller count seen in two real runs of tools/sim/ros/run.sh
# (2026-10-20), so the normal run-to-run spread passes but a blank map or a missing object fails.
MIN_CELLS = {                    # seen in run 1 / run 2
    'north wall':    40,       # 190 /  81
    'south wall':   125,       # 250 / 275
    'west wall':     66,       # 133 / 152
    'east wall':     97,       # 195 / 242
    'red box':       12,       #  24 /  26
    'blue pillar':    6,       #  12 /  12
    'green block':   24,       #  48 /  48
}
MIN_OCCUPIED = 347               # 747 / 694
MIN_FREE = 6329                  # 12659 / 12730


def read_yaml(path):
    """The few keys map_saver writes, without needing PyYAML."""
    meta = {}
    for line in open(path):
        key, _, value = line.partition(':')
        meta[key.strip()] = value.strip()
    origin = [float(v) for v in meta['origin'].strip('[]').split(',')]
    return meta['image'], float(meta['resolution']), origin


def read_pgm(path):
    """A binary (P5) PGM: returns width, height and the rows, top row first."""
    data = open(path, 'rb').read()
    fields, pos = [], 0
    while len(fields) < 4:                    # magic, width, height, maxval
        while data[pos:pos + 1].isspace():
            pos += 1
        if data[pos:pos + 1] == b'#':         # comment line
            pos = data.index(b'\n', pos)
            continue
        end = pos
        while not data[end:end + 1].isspace():
            end += 1
        fields.append(data[pos:end])
        pos = end
    width, height = int(fields[1]), int(fields[2])
    pixels = data[pos + 1:]
    return width, height, [pixels[r * width:(r + 1) * width] for r in range(height)]


def main():
    yaml_path = sys.argv[1]
    image, res, origin = read_yaml(yaml_path)
    width, height, rows = read_pgm(os.path.join(os.path.dirname(yaml_path), image))
    print(f'map: {width} x {height} cells of {res:.2f} m = {width * res:.1f} m x {height * res:.1f} m')
    counts = {0: 0, 254: 0, 205: 0}           # occupied, free, unknown in a trinary map
    for row in rows:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    total = width * height
    print(f'occupied {counts[0]} ({100 * counts[0] / total:.0f} %), free {counts[254]} '
          f'({100 * counts[254] / total:.0f} %), unknown {counts[205]} ({100 * counts[205] / total:.0f} %)')
    failed = []
    if counts[0] < MIN_OCCUPIED:
        failed.append(f'only {counts[0]} occupied cells in the map, need {MIN_OCCUPIED}')
    if counts[254] < MIN_FREE:
        failed.append(f'only {counts[254]} free cells in the map, need {MIN_FREE}')

    def cell(x, y):                           # map coordinates -> pixel value (row 0 = top = max y)
        col = int((x - origin[0]) / res)
        row = height - 1 - int((y - origin[1]) / res)
        return rows[row][col] if 0 <= col < width and 0 <= row < height else None

    for name, (cx, cy, hx, hy) in OBJECTS.items():
        # look for occupied cells in the object's footprint plus one cell all round
        found = 0
        steps_x, steps_y = int(2 * (hx + res) / res) + 1, int(2 * (hy + res) / res) + 1
        for i in range(steps_x):
            for j in range(steps_y):
                if cell(cx - hx - res + i * res, cy - hy - res + j * res) == 0:
                    found += 1
        verdict = 'found' if found >= MIN_CELLS[name] else 'TOO FEW' if found else 'MISSING'
        print(f'{name:12s} at ({cx:+.1f}, {cy:+.1f}): {verdict} ({found} occupied cells)')
        if verdict != 'found':
            failed.append(f'{name}: {found} occupied cells, need {MIN_CELLS[name]}')
    for reason in failed:
        print('FAIL: ' + reason)
    return 1 if failed else 0              # exit code 1: the map does not match the world


if __name__ == '__main__':
    sys.exit(main())
