# Guesser data runbook

## 1. Set up the CPU-only environment

Run the [README setup](README.md#setup) from `models/guesser/data/`. Dependencies use uv, Python 3.13 and the committed lock. No model weights or PyTorch install is needed for data preparation. The separate `../evaluation/` notebook workspace keeps Python 3.12 and its own lock.

## 2. Download, clean and sample

```powershell
$profile = "medium"  # Choose production, medium or small.
.\guesser-data.ps1 download --profile $profile
```

Without `--profile`, this selects the unchanged `production` size. All three training profiles preserve all 345 official category IDs:

| Profile | Reserve/category | Train/category | Validation/category | Test/category | Final total |
|---|---:|---:|---:|---:|---:|
| `production` (default) | 5,500 | 4,000 | 500 | 500 | 1,725,000 |
| `medium` | 2,200 | 1,600 | 200 | 200 | 690,000 |
| `small` | 550 | 400 | 50 | 50 | 172,500 |

For a smaller download and training run, select a profile on every command:

```powershell
.\guesser-data.ps1 download --profile medium
.\guesser-data.ps1 prepare --profile medium
.\guesser-data.ps1 preview --profile medium   # optional
.\guesser-data.ps1 export --profile medium
```

Use `small` instead of `medium` for 500 final originals/category. Output stays separate under `.local/data/production/`, `.local/data/medium/` and `.local/data/small/`. The profile changes original-drawing counts, not the model's batch size.

Production reads selected raw sources from beginning to end. The dated bundled inventory totals about 181.43 GiB; streaming avoids storing full raw files, but those bytes still transfer. Medium and small stop after collecting their candidate reserve from each source's beginning, so they transfer less. Malformed records and repeated IDs do not add reserve slots. Prefix sampling is not uniform sampling of the complete source, and actual bytes depend on drawing length. No source download was run to implement these sizes.

Two categories stream concurrently by default. Cleaning preserves chronology, pauses, single-point strokes, nonzero start times and valid `recognized=false` records. It removes exact repeated points/empty strokes and rejects malformed/nonfinite/unsafe coordinates, invalid times, zero duration and drawings with no extent. IDs remain strings.

Selection uses `SHA256("select-v1|198173|<drawing_id>")` and string ID to rank the retained candidates. Production samples the full file into 5,500 slots; medium and small collect 2,200 and 550 distinct cleaned IDs before stopping. Retained conflicting IDs keep their slot and are flagged for quarantine; uninspected/discarded records have no conflict-tracking guarantee. Production receipts follow whole-file byte-count/MD5 verification. Smaller profiles record their generation, consumed byte count and candidate hash with `source_kind=quickdraw_partial`, `complete=false` and `full_source_verified=false`; those flags describe the source file, not whether the requested sample finished. Matching completed samples resume; interrupted categories restart at zero. Existing compatible production receipts remain usable.

```powershell
.\guesser-data.ps1 download --profile $profile --class "cat" --class "alarm clock" --concurrency 1
```

A class selection follows the profile: production reads each chosen file completely, while medium/small stop at their reserve. No global download cap, source SQLite index or automatic conflict re-download is used.

## 3. Prepare originals and splits

```powershell
.\guesser-data.ps1 prepare --profile $profile
```

One temporary SQLite index checks retained IDs/content/labels and exact full x/y/t trajectories across classes. Conflicts are quarantined, never relabeled. Same-label exact trajectories keep the best-ranked representative. Optional `excluded-ids.txt` entries remain excluded.

Eligible originals are ordered by the separate `split-v1` hash plus ID. The selected profile sets the exact train/validation/test counts: production 4,000/500/500, medium 1,600/200/200, small 400/50/50. All prefixes of an original stay in that split. Original records go directly to `prepared/records/{split}/cNNN.jsonl`, with Parquet manifests under `prepared/manifests/`. Offsets are UTF-8 byte offsets into uncompressed JSONL. The temporary index is removed; candidates are retained. No selected/staging-selected copies are created.

If a class is short, use the explicit refill command in the error, for example:

```powershell
.\guesser-data.ps1 download --profile medium --class "alarm clock" --candidates 3200
.\guesser-data.ps1 prepare --profile medium
```

Preparation does not start network transfers. `dataset-summary.json` contains actual labels, counts, source information and record/manifest hashes. It does not bind the data to README or code-file hashes.

## 4. Optionally inspect examples

```powershell
.\guesser-data.ps1 preview --profile $profile
```

Open `<data-root>/<profile>/preview/index.html` for the selected size. Sheets use training originals only. There are no approval CSVs, reviewers or sign-offs. To omit an individual drawing, put its ID in `<profile>/excluded-ids.txt`, prepare again, and refill only if needed. A legacy nonempty exclusion list is adopted once when no text list exists.

## 5. Check once and export

```powershell
.\guesser-data.ps1 export --profile $profile
```

Export performs one final audit of prepared counts, IDs/trajectories across splits, metadata, byte offsets and data hashes, then writes separate trainer and held-out-test ZIP64 packages plus checksums. There is no freeze command. `audit` is available for an optional standalone check; it is not another required step.

A new export rechecks actual data. If prepared data differs from its summary, prepare it again. A documentation edit does not require re-preparing data. Older prepared data without the new summary can be adopted by this audit. Historical exports are not automatically rebuilt.

Archives are named `trainer-<profile>.zip` and `held-out-test-<profile>.zip` under that profile's export directory.

The trainer archive contains train/validation records and manifests, labels, summary, installable data source and uv setup. It excludes held-out-test records, test manifests and QA images. Keep the held-out archive with the validation owner. Verify transfer checksums and extract before using byte offsets.

## 6. Load one drawing and create its image

```text
Prepared originals on disk
    -> 05-loader.py reads one original
    -> 06-images.py cuts at the chosen elapsed time
    -> renders only visible strokes
    -> foreground/edges preprocessing, fit/pad to 224x224, normalization
    -> one float32 [3,224,224] image plus a class label
    -> PyTorch DataLoader batches images in the model project (future work)
```

```python
from guesser_data import IndexedDrawings

candidate = "foreground"  # Change to "edges" to use edge detection.
prepared = ".local/data/medium/prepared"  # Or production/small; exported package: "prepared".
with IndexedDrawings(prepared, "train") as drawings:
    sample = drawings.training_image(0, epoch=0, candidate=candidate)
    if sample["status"] == "ok":
        image = sample["image"]
        target = sample["class_id"]

with IndexedDrawings(prepared, "validation") as drawings:
    for view in drawings.evaluation_images(0, candidate=candidate):
        print(view["fraction"], view["status"], view["unchanged"])
```

Use the same frozen profile and its train/validation/test packages throughout an experiment. Different profiles have different held-out originals, so their scores alone do not isolate the effect of dataset size. Medium and small are trainable, but no accuracy level is guaranteed.

The loader owns a bounded cache per process and reopens handles after multiprocessing/PID changes. A PyTorch Dataset adapter and DataLoader are the model owner's next step. No custom batching engine is included.

Training cuts are seeded by ID/epoch/purpose: 20% complete, otherwise 10%-90% elapsed time; blank views have bounded retries. Evaluation uses ten fixed stages, retaining blank/uncertain/unchanged outcomes. These are elapsed-time fractions, not point-count fractions. Geometry uses only the current prefix.

For live snapshots, use the same preprocessor directly:

```python
from PIL import Image
from guesser_data import preprocess

snapshot = Image.open("canvas.png")
foreground = preprocess(snapshot)  # default
edges = preprocess(snapshot, candidate="edges")
```

Keep one choice consistent for each model. The current foreground choice is provisional, not an accuracy result. Uniform background estimation can be uncertain; edge detection can lose faint evidence or double-outline thick strokes. Both methods return `ok`, `blank` or `uncertain`; usable images are already normalized. Only the image enters ViT; labels are targets, while word/ID/recognized/times are metadata.

## 7. Small examples and remaining measurements

`example` creates a one-class synthetic smoke example under `.local/data/example/smoke/`. `probe` explicitly requests small real-source ranges under `.local/data/probe/smoke/`; those are nonproduction samples, not whole-source checksum proofs. Neither command runs a production scan.

Full-source throughput, peak RAM/disk, dataset-wide quality, model accuracy and GPU capacity remain to be measured by the model/evaluation owners. A full real category is a useful first production measurement. The data tools do not guarantee that only disk space can become a bottleneck.
