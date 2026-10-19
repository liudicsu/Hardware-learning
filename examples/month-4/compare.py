#!/usr/bin/env python3
"""Compare a ROS 2 run with the output a lesson quotes, ignoring what changes from run to run.

usage: compare.py EXPECTED ACTUAL [--tol T] [--mask REGEX]... [--drop REGEX]... [--sort 1]
Masked before comparing: log timestamps, colcon timings, launch process numbers and pids,
DDS GIDs. With --tol, two numbers count as equal if they differ by at most T (absolute) or
T as a fraction of the expected value, whichever is larger: simulated runs are not bit-exact.
--mask REGEX hides one more pattern that legitimately changes between runs.
--drop REGEX leaves out whole lines that match, on both sides: e.g. action feedback, whose
number of lines depends on timing.
--sort 1 compares the lines in sorted order: several processes log in parallel, so their
lines can interleave differently on every run.
Prints "same" or a diff; exit code 1 on a difference."""
import difflib, re, sys

def mask(text, extra=()):
    for rx in extra:
        text = re.sub(rx, '<masked>', text)
    text = re.sub(r'\[(DEBUG|INFO|WARN|ERROR|FATAL)\] \[\d+\.\d+\]', r'[\1] [T]', text)
    text = re.sub(r'\[\d+(\.\d+)?s\]', '[Ts]', text)            # colcon: [0.68s]
    text = re.sub(r'\[([A-Za-z_][\w-]*)-\d+\]', r'[\1-N]', text)   # launch: [hello_node-1]
    text = re.sub(r'\bpid \[?\d+\]?', 'pid N', text)
    text = re.sub(r'log files can be found below \S+', 'log files can be found below LOGDIR', text)
    text = re.sub(r'_ros2cli_\d+', '_ros2cli_N', text)
    text = re.sub(r'GID: [0-9a-f.]+', 'GID: X', text)
    text = re.sub(r'[ \t]+$', '', text, flags=re.M)
    return text.rstrip('\n') + '\n'

NUM = re.compile(r'-?\d+(?:\.\d+)?(?:e[-+]?\d+)?')

def close(a, b, tol):
    ta, tb = NUM.split(a), NUM.split(b)
    na, nb = NUM.findall(a), NUM.findall(b)
    if ta != tb or len(na) != len(nb):
        return False
    return all(abs(float(x) - float(y)) <= max(tol, tol * abs(float(x))) for x, y in zip(na, nb))

def main():
    exp, act = open(sys.argv[1]).read(), open(sys.argv[2]).read()
    tol, extra, drop, sort, args = 0.0, [], [], False, sys.argv[3:]
    while args:
        opt, val, args = args[0], args[1], args[2:]
        if opt == '--tol':
            tol = float(val)
        elif opt == '--mask':
            extra.append(val)
        elif opt == '--drop':
            drop.append(re.compile(val))
        elif opt == '--sort':
            sort = val == '1'
    e, a = mask(exp, extra).splitlines(), mask(act, extra).splitlines()
    e = [l for l in e if not any(rx.search(l) for rx in drop)]
    a = [l for l in a if not any(rx.search(l) for rx in drop)]
    if sort:
        e, a = sorted(e), sorted(a)
    if len(e) == len(a) and all(x == y or (tol and close(x, y, tol)) for x, y in zip(e, a)):
        return 0
    sys.stdout.writelines(l + '\n' for l in difflib.unified_diff(e, a, 'expected', 'this run', lineterm=''))
    return 1

if __name__ == '__main__':
    sys.exit(main())
