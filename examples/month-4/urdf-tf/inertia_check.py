#!/usr/bin/env python3
"""Check the <inertial> of every link in a URDF before Gazebo does it the hard way.

usage: xacro robot.urdf.xacro > robot.urdf && python3 inertia_check.py robot.urdf

Flags links that a physics engine cannot simulate: no inertial at all (fine only for
massless frames such as base_footprint or camera_link), a mass of zero or less, a
non-positive moment of inertia, or moments that break the triangle rule
(Ixx + Iyy >= Izz and so on), which no real object can have."""
import sys
import xml.etree.ElementTree as ET


def main(path):
    robot = ET.parse(path).getroot()
    total, problems = 0.0, 0
    print(f'{"link":20} {"mass kg":>8} {"Ixx":>10} {"Iyy":>10} {"Izz":>10}  check')
    for link in robot.findall('link'):
        name = link.get('name')
        inertial = link.find('inertial')
        if inertial is None:
            print(f'{name:20} {"-":>8} {"":>10} {"":>10} {"":>10}  no inertial (frame only)')
            continue
        m = float(inertial.find('mass').get('value'))
        i = inertial.find('inertia')
        ixx, iyy, izz = (float(i.get(k)) for k in ('ixx', 'iyy', 'izz'))
        ok = m > 0 and min(ixx, iyy, izz) > 0 and \
            ixx + iyy >= izz and iyy + izz >= ixx and ixx + izz >= iyy
        problems += not ok
        total += m
        print(f'{name:20} {m:8.3f} {ixx:10.3e} {iyy:10.3e} {izz:10.3e}  {"ok" if ok else "BAD"}')
    print(f'total mass {total:.3f} kg, {problems} problem(s)')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
