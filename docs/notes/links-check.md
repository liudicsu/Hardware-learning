# External link check — run of 2026-10-22

`python3 tools/check_links.py` (standard library only, manual, **not in CI**; see README).

Result on the box network: 190 unique URLs on 89 hosts. The run predates the merge of #17, #18 and #20; `--list` now finds 198. 172 OK, 3 FAIL, 15 BLOCKED, 0 ALLOWED.

FAIL — all three are timeouts from this network, not dead pages:
- http://brettbeauregard.com/blog/2011/04/improving-the-beginners-pid-introduction/ — the page loads from a second network (checked 2026-10-22).
- https://www.solidworks.com/solution/solidworks-makers — the page loads from a second network (checked 2026-10-22).
- http://www.ros.org/wiki/xacro — wiki.ros.org answers 403 to automated fetches. Open it in a browser to confirm.

BLOCKED (401/403/429, bot protection or shop rate limits; check them in a browser before changing anything):
ctms.engin.umich.edu, github.com blob link (429), openelab.com, allaboutcircuits.com, autodesk.com, elegoo.com (×2),
mathworks.com videos (×4), printables.com, robotshop.com, udemy.com (×2).

fbswiki.org: the root https://fbswiki.org/ answers 200, but chapter pages such as
`/wiki/index.php/Feedback_Systems_by_Astrom_and_Murray` answer 500. The math reference therefore links to the site root.
Switch to the chapter pages once they load again.

Nothing was changed in the URLs based on this run. No link is dead. The `ALLOW` table in the script is empty.
