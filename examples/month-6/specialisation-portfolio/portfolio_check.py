"""portfolio_check.py: check a project README for what a reviewer looks for in the first two minutes.

usage: python3 portfolio_check.py PROJECT_DIR [PROJECT_DIR ...]      (exit code 1 if anything is missing)

It reads PROJECT_DIR/README.md and looks for eight things, by simple text rules (it cannot judge quality,
only whether the part is there):
  video         a link to a video or animation (YouTube, Bilibili, Vimeo, .mp4, .gif, .webm)
  result        a success count written as k/n, or a measured number with a unit, in a table row
  trials        the number of trials or test conditions stated in words ("20 trials", "10 positions")
  failures      a section on failures (heading containing "failure" or "失败")
  reproduce     a section on reproducing it (heading with "reproduce", "how to run" or "复现") with a code block
  hardware      a section listing the hardware (heading with "hardware", "bill of materials", "BOM" or "硬件")
  contribution  what you did yourself versus reused (heading with "my part", "what I built", "credits" or "贡献")
  next          limitations or next steps (heading with "limitation", "next step" or "局限", "下一步")
Standard library only.
"""
import os
import re
import sys

UNIT = r'(?:mm|cm|m|s|ms|Hz|deg|°|%|N|g|kg|V|A|mA)'
CHECKS = [
    ('video', 'a video or GIF of it working',
     lambda t, h: re.search(r'(youtube\.com|youtu\.be|bilibili\.com|vimeo\.com|\.mp4|\.gif|\.webm)', t, re.I)),
    ('result', 'a results table with k/n or measured numbers',
     lambda t, h: re.search(r'^\|.*(\b\d+\s*/\s*\d+\b|\d(?:\.\d+)?\s*' + UNIT + r'\b).*\|\s*$', t, re.M)),
    ('trials', 'how many trials or conditions were tested',
     lambda t, h: re.search(r'\b\d+\s+(trials|runs|attempts|positions|episodes)\b|\d+\s*(次试验|次运行|个位置)', t, re.I)),
    ('failures', 'a failure analysis section',
     lambda t, h: any(re.search(r'failure|失败', x, re.I) for x in h)),
    ('reproduce', 'how to reproduce it, with commands',
     lambda t, h: any(re.search(r'reproduce|how to run|复现', x, re.I) for x in h) and '```' in t),
    ('hardware', 'the hardware or bill of materials',
     lambda t, h: any(re.search(r'hardware|bill of materials|\bBOM\b|硬件', x, re.I) for x in h)),
    ('contribution', 'what you built yourself versus reused',
     lambda t, h: any(re.search(r'my part|what i built|credits|贡献', x, re.I) for x in h)),
    ('next', 'limitations or next steps',
     lambda t, h: any(re.search(r'limitation|next step|局限|下一步', x, re.I) for x in h)),
]


def check(project):
    path = os.path.join(project, 'README.md')
    with open(path, encoding='utf-8') as f:
        text = f.read()
    headings = [line.lstrip('#').strip() for line in text.splitlines() if line.startswith('#')]
    words = len(re.findall(r'\w+', text))
    print(f'{os.path.basename(os.path.normpath(project))}: README.md, {words} words, {len(headings)} headings')
    missing = 0
    for name, what, rule in CHECKS:
        ok = bool(rule(text, headings))
        missing += not ok
        print(f'  {"ok     " if ok else "MISSING"} {name:<13} {what}')
    print(f'  {len(CHECKS) - missing} of {len(CHECKS)} present')
    return missing


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip().splitlines()[2])
    missing = 0
    for i, project in enumerate(sys.argv[1:]):
        if i:
            print()
        missing += check(project)
    sys.exit(1 if missing else 0)


if __name__ == '__main__':
    main()
