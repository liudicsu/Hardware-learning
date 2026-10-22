#!/usr/bin/env python3
"""check_links.py: find external URLs in the course sources and report the ones that do not answer 2xx/3xx.

Manual tool, NOT run in CI (external sites change, rate-limit and block bots; a CI failure caused by a
third-party outage would block unrelated PRs). Run it before a release or when a reader reports a dead link:

    python3 tools/check_links.py                 # check every URL, print a summary and the failures
    python3 tools/check_links.py --list          # only list the URLs found (no network)
    python3 tools/check_links.py --json out.json # also write every result as JSON
    python3 tools/check_links.py --workers 8 --timeout 20

Scanned: src/content/**/*.mdx, src/lib/*.ts (curriculum, resources, glossary, math reference, ...),
messages/*.json and examples/**/README*. URLs are taken from markdown links, href/url props and bare
http(s) URLs. Each URL is requested with HEAD, falling back to GET when the server rejects HEAD
(405/403/501 or a network error), following redirects, with a browser-like User-Agent.
A URL that times out is retried once with twice the timeout.

Results are sorted into three groups:
  OK       2xx/3xx.
  BLOCKED  401/403/429: usually bot protection (Cloudflare, shop rate limits) rather than a dead link.
           Open these in a browser before changing anything; they do not affect the exit code.
  FAIL     404/410, other 4xx/5xx, DNS/TLS errors, timeouts after the retry.
Exit code: 0 if nothing is in FAIL, 1 otherwise. Standard library only (Python >= 3.10).

Known exceptions can be listed in ALLOW below with the reason; they are reported as ALLOWED.
XML namespace names (xmlns="..."), URLs containing shell/template variables ($, ${...}, {...}) and placeholder hosts (*.local,
localhost, example.com) and the site itself are skipped.
"""
import argparse
import concurrent.futures as cf
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOBS = ["src/content/**/*.mdx", "src/lib/*.ts", "messages/*.json", "examples/**/README*"]
URL = re.compile(r"https?://[^\s\"'<>()\[\]{}`|\\]+")
TRAILING = ".,;:!?*_"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36 hl-check-links"
SKIP_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "example.com", "liudicsu.github.io", "local")
BLOCKED = (401, 403, 429)
# url prefix -> reason; answered non-2xx/3xx is reported as "allowed", not as a failure
ALLOW: dict[str, str] = {}


def find_urls():
    found: dict[str, set[str]] = {}
    for pattern in GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            text = path.read_text(encoding="utf-8", errors="replace")
            for n, line in enumerate(text.splitlines(), 1):
                for m in URL.finditer(line):
                    if re.search(r"xmlns(:\w+)?=[\"']?$", line[: m.start()]):
                        continue  # an XML namespace name (e.g. xacro's), not a link
                    url = m.group().rstrip(TRAILING)
                    host = re.sub(r"^https?://", "", url).split("/")[0].split(":")[0]
                    if any(host == h or host.endswith("." + h) for h in SKIP_HOSTS):
                        continue
                    if "$" in url or "{" in url:
                        continue
                    found.setdefault(url, set()).add(f"{path.relative_to(ROOT)}:{n}")
    return found


def request(url, method, timeout):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.status


def check(url, timeout):
    status, err = check_once(url, timeout)
    if status == 0 and "imed out" in err:
        status, err = check_once(url, timeout * 2)
    return status, err


def check_once(url, timeout):
    try:
        return request(url, "HEAD", timeout), ""
    except urllib.error.HTTPError as e:
        if e.code not in (403, 404, 405, 429, 500, 501, 503):
            return e.code, ""
    except Exception:
        pass
    try:
        return request(url, "GET", timeout), ""
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # DNS, TLS, timeout
        return 0, type(e).__name__ + ": " + str(e)[:80]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true", help="only list URLs, no network")
    ap.add_argument("--json", help="write all results to this JSON file")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=float, default=20)
    args = ap.parse_args()
    found = find_urls()
    if args.list:
        for url in sorted(found):
            print(url)
        print(f"{len(found)} unique URLs")
        return 0
    results = {}
    with cf.ThreadPoolExecutor(args.workers) as ex:
        futs = {ex.submit(check, u, args.timeout): u for u in found}
        for f in cf.as_completed(futs):
            results[futs[f]] = f.result()
    ok = [u for u, (s, _) in results.items() if 200 <= s < 400]
    bad = sorted(u for u in results if u not in ok)
    allowed = [u for u in bad if any(u.startswith(p) for p in ALLOW)]
    blocked = [u for u in bad if u not in allowed and results[u][0] in BLOCKED]
    failed = [u for u in bad if u not in allowed and u not in blocked]
    hosts = len({re.sub(r"^https?://", "", u).split("/")[0] for u in found})
    print(f"{len(found)} unique URLs on {hosts} hosts: {len(ok)} OK (2xx/3xx), {len(failed)} FAIL, "
          f"{len(blocked)} BLOCKED (401/403/429, check in a browser), {len(allowed)} ALLOWED")
    for u in failed + blocked + allowed:
        s, err = results[u]
        tag = "ALLOWED" if u in allowed else "BLOCKED" if u in blocked else "FAIL"
        print(f"{tag} {s or 'ERR'} {u} {err}".rstrip())
        for where in sorted(found[u])[:3]:
            print(f"      {where}")
    if args.json:
        Path(args.json).write_text(json.dumps({u: {"status": s, "error": e, "where": sorted(found[u])} for u, (s, e) in sorted(results.items())}, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
