# Batch-7 citation polish / 引文补充

Base811eb6c, fresh fix/batch7-polish worktree /workspace/hl-b7polish. Citation-only: no minutes/toy code/expected/workflow changes. Site23610,71 lessons; all existing minute locks kept. Node dependencies hardlinked from prior worktree.

Opened on2026-11-06 Asia/Shanghai (UTC+8). Exact results below, not inferred from search snippets. No HTTP failure is called200.

| Request | Result | Selection |
|---|---|---|
| https://users.ece.cmu.edu/~koopman/crc/ |200| Primary researcher-maintained CRC tables / CRC Zoo entry point; read actual page and its notation/HD caveats |
| https://users.ece.cmu.edu/~koopman/roses/dsn04/koopman04_crc_poly_embedded.pdf |200| Selected author-hosted DSN2004 preprint; PDF extracted/read, author/title confirmed |
| https://doi.org/10.1109/34.121791 |302 to HTTP IEEE, then500 via curl; WebFetch403| Not used as a broken clickable reading URL; DOI identifier printed as text |
| Same Besl DOI with documented Accept: application/vnd.citationstyles.csl+json |200, resolves to Crossref /v1/works/10.1109%2F34.121791/transform| Bibliographic metadata confirms title, authors, TPAMI14(2),239–256, February1992; not full-text access |
| https://graphics.stanford.edu/~smr/ICP/comparison/besl-mckay-icp-pami92.pdf |200| Selected working original-paper PDF copy; scanned title page rendered/read and matches DOI metadata |
| https://doi.org/10.1109/ROBOT.1991.132043 |302 to HTTP IEEE, then500 via curl| Conference alternative not cited as a clickable reading link |
| HTTPS IEEE /document/121791/ and /document/132043/ |202 with empty response bodies| Not claimed as readable200 article pages |
| https://doi.org/10.1016/0262-8856(92)90066-C |200 at linkinghub.elsevier.com/retrieve/pii/026288569290066C| Selected journal DOI; response is a redirect stub, not full paper access |
| Same Chen journal DOI with documented CSL-JSON Accept header |200 at Crossref transform| Confirms British-spelling title, Chen/Medioni, IVC10(3),145–155, April1992; no claim full paper read |
| Initial guessed https://users.ece.cmu.edu/~koopman/pubs/koopman04_crc_poly_embedded.pdf |404| Excluded; correct author-hosted /roses/dsn04/ PDF above was then discovered, opened and verified200 |

Only the successful opened sources are added to resources. For Besl–McKay, a working original-paper PDF is the reading link rather than the failing browser-style DOI landing chain; the DOI itself was successfully resolved in its citation-metadata representation. For Chen–Medioni choose the working1992 journal DOI rather than the failing1991 conference route. Availability details stay here, not as review/process chatter in lessons.

New en/zh paragraphs are bibliographic further reading only. Existing secondary CRC reference and Open3D tutorial remain labelled and all toy/model caveats remain unchanged. No new algorithm claims or paper-performance numbers.

## Validation

All193 prior expected files byte-identical to811eb6c, no example files changed, all71 lesson minute values identical (site23610). Only citation paragraphs/cards, catalogue resource IDs, this audit and citation locks change. No Summary, exercise, toy, plan, minute or workflow edits.

Passed all requested local checks: check_diagrams (23 diagrams /11948 checks), widgets (680), Wokwi (8 diagrams /16 cards), quotes (362 code blocks /302 outputs), all eleven month harnesses, lint, next typegen, tsc --noEmit, production build/postbuild (178 pages) and diff whitespace. Existing optional local CAD/SDK/ROS2/MuJoCo skips remain unchanged; all stdlib checks run.
