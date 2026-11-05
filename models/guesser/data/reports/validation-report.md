> Historical report: this describes an earlier validation workflow. Current numbered stages, settings and approval-free export behavior are documented in [the runbook](../RUNBOOK.md). Existing data/ZIPs were not regenerated for the slim refactor.

# Bounded Guesser data validation

**Passed — 5 November 2026.** The package is implemented, its data checks pass, and the user approved all ten real-source smoke class sheets. The approved smoke package was frozen, audited, exported separately by custody, and reopened. No full category file or full dataset was downloaded.

## Results

| Validation stage | Classes | Training originals | Validation originals | Test originals | Result |
|---|---:|---:|---:|---:|---|
| Synthetic all-label fixture | 345 | 5,520 | 690 | 690 | Passed; 16/2/2 per class |
| Synthetic production-count fixture | 1 | 4,000 | 500 | 500 | Passed; exact intended production counts |
| Partial real-source smoke | 10 | 160 | 20 | 20 | Passed; user-reviewed and frozen |

Synthetic fixture records and their archives are explicitly marked synthetic validation data. Real-source smoke is marked validation-only and `trainable=false`; it is not synthetic and cannot satisfy production completion checks. The 345-label fixture does not establish production-wide source quality or accuracy.

**37 data-only checks passed** in the final suite. They cover deterministic sampling and string-ID tie-breaking, metadata/content conflicts before heap admission, cleaning and canonical numbers, signed zero, timestamps/pauses/dots, corruption and checksum/generation mismatch, interrupted writes, retries, valid range enforcement, persistent budget accounting, reserve refill and resume, global partition disjointness, byte offsets and metadata, review gating/invalidation, P1/P2 repeatability, process-local indexed loading, freeze integrity and separate export contents.

The final archives were checked with ZIP CRCs and SHA-256 and every exported manifest reference was reopened. The extracted trainer archive independently installed with `uv sync --frozen --offline --no-dev`; its command reported version 0.1.0, indexed 160 training/20 validation originals, and generated both P1/P2 views. It contains no test records, test manifest or mixed-split QA images.

## Download accounting

| Item | Observed result |
|---|---:|
| Hard task cap | 104,857,600 bytes (100 MiB) |
| Actual response-body bytes observed, including registry and inventory | 6,779,537 bytes (6.47 MiB) |
| Conservative charged budget, including unrefunded reservations | 8,634,368 bytes (8.23 MiB) |
| Live requests | 12 (two metadata requests and ten probes) |
| Whole Quick, Draw! objects verified | 0 |
| Production scans executed | 0 |

The shared ledger remains at `../.local/download-budget.json`. All live-data operations used that guard. Mock failure/retry checks use isolated local fixtures and make no real requests. No additional dataset download was needed for finalization or the offline export-install check.

Each probe requested a maximum range of 9 MiB, required HTTP 206 with exact Content-Range and generation, and stopped after 200 usable complete records. Receipts record consumed ranges and SHA-256 hashes. They explicitly set `complete=false` and `full_source_verified=false`; **a partial hash is not a whole-object checksum verification**. Probe prefix samples do not have the unbiased full-file sampling property of production acquisition.

The ten inspected categories were circle, line, cat, bicycle, alarm clock, coffee cup, The Eiffel Tower, animal migration, airplane and zigzag. The official registry has 345 labels in its preserved source order; its SHA-256 is `6326fde883ce71b53153bdf50b3671dc6652c8c14e67c7d07d23c1af6d103f4b`.

## Preprocessing and review

Both candidates produce float32 `[3,224,224]` images for usable visible states. There are 17 synthetic visible-state stress cases, covering colored backgrounds/strokes, similar luminance, interior/background fills, erased/restored evidence, blank images, thin/thick strokes, low contrast and border contact. Source and processed sheets and tensor hashes are saved locally. They validate preprocessing behavior, not game-canvas accuracy or frontend operation replay.

The P1 and P2 configuration hashes are in [the machine-readable report](validation-report.json), configs, fixtures and exported code. P1 retains filled silhouettes; P2 can produce double boundaries and lose low-contrast evidence. The final candidate remains unselected pending the model-validation pilot. The frozen package also fingerprints code, dependency lock and artifacts; the configuration hash alone is not an implementation hash.

The user explicitly approved **all ten smoke class sheets**, with no exclusions. That approval is recorded in the review CSV/decisions and bound to the selected class membership. The final code audit tightened canonical serialization and ID/content conflict checks; the original/manifests were verified unchanged before refreshing only validation markers. No review was fabricated for real sources.

## Local artifacts

Generated records, images, environments and exports are intentionally ignored by Git and remain on E:.

- [Real-source review sheets](../.local/data/validation/real-source/smoke/qa/index.html)
- [P1 processed stress sheet](../.local/data/validation/stress/p1-processed.png)
- [P2 processed stress sheet](../.local/data/validation/stress/p2-processed.png)
- [Trainer smoke archive — 180 originals](../.local/data/validation/real-source/smoke/exports/trainer-validation_only.zip)
- [Held-out smoke archive — 20 originals](../.local/data/validation/real-source/smoke/exports/held-out-test-validation_only.zip)
- [Smoke export checksums](../.local/data/validation/real-source/smoke/exports/checksums.json)
- [Detailed report](validation-report.json)
- [Production teammate runbook](../RUNBOOK.md)

All fixture packages also remain under `../.local/data/validation/`. Freeze/audit fingerprints were refreshed after the final source corrections, and the final packages were reopened again without fetching source data.

## What remains for the model teammate

The tooling is ready for the explicit production workflow in the runbook. The teammate must still perform the full generation-pinned streams, confirm all-class 4,000/500/500 counts after global conflicts/refills, measure actual production throughput/memory, and complete the 345-class quality review. No dataset-wide quality, model accuracy or real-game performance claim follows from this smoke package. P1/P2 selection, model training and final held-out evaluation remain outside this data implementation.

The environment uses Python 3.13.5 and uv 0.12.18. `uv.lock` pins NumPy 2.5.4, Pillow 13.0.0, PyArrow 26.0.1, OpenCV headless 5.0.0.93, google-crc32c 1.9.0 and psutil 7.2.2; pytest is a locked development dependency. Environments, uv cache and temporary/generated files are on E:. No frontend checks, new human drawing collection, model download/training or deployment were performed.

## Folder organization update

The package moved from `guesser-data/` to `models/guesser/data/` on 5 November 2026. Artifact links now use the new location. The validation results above are from the completed implementation run; no tests or dataset downloads were rerun for this move. Drawing records, class membership, approvals and the existing exported archive bytes remain unchanged.

## Readability refactor update

The data source was simplified and formatted with Ruff on 5 November 2026. All 37 data regression checks passed, along with exact image/view comparisons. Existing prepared data, split membership and approvals were unchanged; the six local handoff archives were rebuilt with the readable source and updated checksums. Previous archives are preserved under `.local/readability-before/exports/`. See the readability review for details. No new dataset download or training run was performed.

## Type fixes, simpler acquisition and P1 default

On 5 November 2026, the team chose P1 as the provisional default and kept P2 available through `candidate="p2"`. The runbook now uses one candidate consistently across training and validation and shows both snapshot preprocessing calls. This records a team choice, not an accuracy result.

The global download-budget feature was removed at the user's request: no ledger reads/writes, cross-process locks, byte reservations, counters or `--max-download-mib` option remain in the commands. Historical download totals above describe the initial validation run only. Validation still uses small prefix samples; production scanning is explicit and has no global cap. Acquisition remains in one file, reduced from 714 to 611 lines. Its SQLite operations run automatically to check IDs/conflicts without holding every source record in memory.

Fixed all five reported Pyright errors, including a non-exception class in a malformed-record handler, an optional class list/exception, diagnostic value types and a fixed-size image resize tuple. Pyright is a uv-locked development dependency. Ruff and Pyright passed; all 37 data-only regressions passed in 28.99 seconds. A malformed-record regression replaced the obsolete budget test. Both P1/P2 image outputs, seeded views, timestamp cuts and all 17 stress fixtures exactly matched the saved baseline.

All three existing local validation workspaces were reaudited and their six archives rebuilt/reopened with current source, config and instructions. Original data, manifests, membership and approvals stayed unchanged. Previous archives and freeze markers are preserved in `.local/type-fix-before/exports/`. No new dataset downloads, model training, frontend checks, commits or pushes were performed for this update.
