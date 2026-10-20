#!/usr/bin/env python3
"""Check that what the lessons quote is what the repository holds, for every month.

usage: python3 tools/check_quotes.py          (from anywhere; exit code 1 on any problem)

1. Code: every fenced block directly under a <CodeSource path="..." /> line must be
   byte-for-byte the file at that path.
2. Simulated outputs: every fenced block inside <SimOutput source="..."> ... </SimOutput>
   must appear, byte-for-byte and on whole lines, in one of the expected-output files
   (tools/sim/expected/*.txt or examples/month-*/expected/*.txt) that the reproduce and
   check scripts compare their runs against.

The one exception (docs/CONTENT_GUIDE.md, "Comparing quotes with the repo"): shell command
lines at the START of a quoted block, i.e. leading lines that begin with "$ ", are left out
of the comparison. They show the reader what to type; the expected file may or may not record
the prompt. Every other line, including "$ " lines further down the block, still compares
byte-for-byte."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CODE = re.compile(r'<CodeSource path="([^"]+)" />\n\n(```+)[^\n]*\n(.*?)\n\2\n', re.S)
SIM = re.compile(r'<SimOutput source="(\w+)"[^>]*>\n\n(```+)[^\n]*\n(.*?)\n\2\n\n</SimOutput>', re.S)


def drop_leading_commands(body):
    """Leave out the shell command lines ("$ ...") at the start of a block, nothing else."""
    lines = body.split('\n')
    while lines and lines[0].startswith('$ '):
        lines.pop(0)
    return '\n'.join(lines)


def main():
    expected = [p.read_text() for p in sorted(ROOT.glob('tools/sim/expected/*.txt'))]
    expected += [p.read_text() for p in sorted(ROOT.glob('examples/month-*/expected/*.txt'))]
    expected = ['\n' + t.rstrip('\n') + '\n' for t in expected]
    bad = n_code = n_sim = 0
    for f in sorted(ROOT.glob('src/content/*/*/*.mdx')):
        rel, text = f.relative_to(ROOT), f.read_text()
        for m in CODE.finditer(text):
            n_code += 1
            path = ROOT / m.group(1)
            if not path.is_file():
                print(f'MISSING  {rel}: {m.group(1)} does not exist'); bad += 1
            elif path.read_text().rstrip('\n') != drop_leading_commands(m.group(3)).rstrip('\n'):
                print(f'DIFF     {rel}: code block differs from {m.group(1)}'); bad += 1
        if text.count('<CodeSource') != len(CODE.findall(text)):
            print(f'LAYOUT   {rel}: a <CodeSource> is not followed by a blank line and a fence'); bad += 1
        for m in SIM.finditer(text):
            n_sim += 1
            body = drop_leading_commands(m.group(3))
            if not body.strip():
                print(f'EMPTY    {rel}: a SimOutput block holds nothing but command lines'); bad += 1
            elif not any('\n' + body + '\n' in t for t in expected):
                first = body.split('\n', 1)[0][:70]
                print(f'NOT IN expected  {rel}: SimOutput block starting "{first}"'); bad += 1
        if text.count('<SimOutput') != len(SIM.findall(text)):
            print(f'LAYOUT   {rel}: a <SimOutput> does not wrap exactly one fenced block'); bad += 1
    print(f'{n_code} code blocks, {n_sim} simulated outputs checked, {bad} problems')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
