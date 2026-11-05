> Historical report: this describes an earlier validation workflow. Current numbered stages, settings and approval-free export behavior are documented in [the runbook](../RUNBOOK.md). Existing data/ZIPs were not regenerated for the slim refactor.

# Guesser data readability review

Completed on 5 November 2026 using the simplify skill's reuse, quality and efficiency review lenses. The scope is the data package's source, existing tests and PowerShell launcher, plus concise repository coding guidelines. Generated data, model behavior and frontend implementation are outside the code-edit scope.

## Readability

- Added four concise code-style rules to the repository AGENTS.md covering Python, TypeScript/React, PowerShell/JSON, and simple library-based implementation.
- Added Ruff as a uv-managed development dependency. Python targets 3.13, four-space indentation and an 88-column formatter, with import and basic correctness/style checks.
- Expanded compound one-line statements, grouped imports, replaced unclear local names, added useful interface types and short docstrings, and made long SQL/messages readable.
- Formatted the PowerShell launcher as normal try/finally blocks while preserving arguments, E: cache/temp paths and exit status.

## Simplifications

| Area | Change |
|---|---|
| Shared file utilities | One atomic-output context now serves byte, JSON and JSONL writers and prepared-record shards. It preserves close/fsync/replace ordering and cleanup on failure. |
| Acquisition | Reused one complete-source opener for status/generation/encoding checks; verified cached candidates by streaming; avoided revalidating the same successful resume receipt. |
| Cleaning | Removed the duplicate list of every point and repeated global bounds scans. Coordinate conversion has one small helper. Pauses, dots, signed-zero normalization and original timing remain. |
| Preparation | Separated candidate indexing, unique selection and split writing. Read source inventory once per operation, removed already-proven duplicate class checks, and computed each handoff-sample priority once. |
| Image views | Made background extraction, edge extraction and final fit/normalization separate, direct functions. Reused the already-resolved configuration for its hash. |
| QA | Read only the eight examples needed for each contact sheet; used the shared hash function and ordinary imports. |
| Indexed loader | Removed duplicate state resets while preserving bounded caches, file cleanup, pickling and per-process handles. |
| CLI | Used clear parser/argument names and one output path for success/errors. Commands, flags, structured messages and exit codes remain. |
| Validation | Used functools.lru_cache for the bounded archive-shard cache and reused freeze's completed audit instead of running the same check again immediately. |

No new framework, factory hierarchy or general-purpose pipeline abstraction was introduced. Existing NumPy, Pillow, OpenCV, PyArrow and SQLite responsibilities remain.

## Preserved requirements

Configuration values, seed, category ordering, sampling priorities, original-level splits, timestamp-prefix rules, rendering, P1/P2 settings and command interface remain unchanged. The download cap, pinned source generation/checksums, conflict quarantine, review approvals, safe publication and separate held-out-test exports are intentional experiment requirements and remain enforced.

## Verification

- Ruff formatting check: passed for all 15 source/test Python files.
- Ruff lint/import check: passed.
- uv lock check: passed offline; Ruff is a development-only addition.
- Existing data regression suite: **37 passed**, with no test cases removed or new dataset downloads.
- Exact before/after output comparison: matched timestamp cuts, seeded training/evaluation views, P1/P2 arrays and all 17 stress-fixture outputs for the saved local baseline.
- Reaudited all three existing local validation workspaces. Prepared originals, manifests, selected membership and human approvals were unchanged before renewing source/package fingerprints.
- Rebuilt and reopened all six small handoff archives with the current readable source. Prior archives remain under `.local/readability-before/exports/`.
- Installed the rebuilt trainer archive using uv entirely offline with development packages excluded. Indexed reads and both preprocessing candidates passed; held-out records and their manifest remain absent from that trainer archive.

This does not claim production-scale throughput or model accuracy. No frontend checks, new dataset downloads, model-weight downloads, model training, commits or pushes were performed for this refactor.

## Type fixes, simpler acquisition and P1 default

On 5 November 2026, the team chose P1 as the provisional default and kept P2 available through `candidate="p2"`. The runbook now uses one candidate consistently across training and validation and shows both snapshot preprocessing calls. This records a team choice, not an accuracy result.

The global download-budget feature was removed at the user's request: no ledger reads/writes, cross-process locks, byte reservations, counters or `--max-download-mib` option remain in the commands. Historical download totals above describe the initial validation run only. Validation still uses small prefix samples; production scanning is explicit and has no global cap. Acquisition remains in one file, reduced from 714 to 611 lines. Its SQLite operations run automatically to check IDs/conflicts without holding every source record in memory.

Fixed all five reported Pyright errors, including a non-exception class in a malformed-record handler, an optional class list/exception, diagnostic value types and a fixed-size image resize tuple. Pyright is a uv-locked development dependency. Ruff and Pyright passed; all 37 data-only regressions passed in 28.99 seconds. A malformed-record regression replaced the obsolete budget test. Both P1/P2 image outputs, seeded views, timestamp cuts and all 17 stress fixtures exactly matched the saved baseline.

All three existing local validation workspaces were reaudited and their six archives rebuilt/reopened with current source, config and instructions. Original data, manifests, membership and approvals stayed unchanged. Previous archives and freeze markers are preserved in `.local/type-fix-before/exports/`. No new dataset downloads, model training, frontend checks, commits or pushes were performed for this update.
