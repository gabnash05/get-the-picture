# Guesser data

A small Python 3.13/uv project for preparing Quick, Draw! originals and creating timed images. Model training and the prediction service belong to their separate model folders.

[Visual walkthrough](../../../docs/guesser/guesser-flow.html): an interactive visualization of this data component, stored alongside the Guesser planning docs.

## Setup

From `models/guesser/data/`:

```powershell
$env:UV_CACHE_DIR = Join-Path $PWD '.local/cache/uv'
$env:TEMP = Join-Path $PWD '.local/tmp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
uv sync --frozen
.\guesser-data.ps1 preflight
```

Use uv to change dependencies and keep `pyproject.toml`/`uv.lock` together. The launcher uses ignored local caches/temp files. Output defaults to `.local/data/production/`; `--data-root` can point to any drive. E: is recommended on this laptop because C: is nearly full.

## Read the files in this order

| Step | Actual implementation |
|---|---|
| 1 | [`01-download.py`](src/01-download.py): download, clean each drawing, keep a deterministic sample and save a completion receipt. |
| 2 | [`02-prepare.py`](src/02-prepare.py): deduplicate retained candidates, split originals, write JSONL/Parquet and a data summary. |
| 3, optional | [`03-preview.py`](src/03-preview.py): training-only contact sheets and a small synthetic example. |
| 4 | [`04-export.py`](src/04-export.py): one final data audit and separate trainer/test ZIPs. |
| 5 | [`05-loader.py`](src/05-loader.py): seek one original and choose its training or evaluation view. |
| 6 | [`06-images.py`](src/06-images.py): cut by time, render visible strokes, preprocess and normalize. |

All implementation files live directly in `src/`. The package settings keep the import name `guesser_data` without requiring another source folder.

The stage files use the requested literal `01-name.py` format. A small standard-library importer loads them; callers can use `from guesser_data import IndexedDrawings, preprocess`.

`settings.py` contains the actual editable defaults. `common.py` contains shared file/hash helpers; `cli.py` routes commands. There are no descriptive JSON configs, approval CSVs, sign-offs or freeze step.

```text
Prepare: 01 download/clean/sample -> 02 deduplicate/split -> 03 optional preview -> 04 check/export
Load:    05 read one drawing -> 06 cut -> render -> preprocess -> one image + class label
         -> PyTorch DataLoader batches images in the model project (future work)
```

## Normal workflow

```powershell
.\guesser-data.ps1 download
.\guesser-data.ps1 prepare
.\guesser-data.ps1 preview   # optional
.\guesser-data.ps1 export
```

`download` is an explicit full-source operation: it reads the category files, not just the retained rows. It resumes matching completed categories and restarts incomplete ones. Production retains initially 5,500 candidates/class, then selects 5,000 distinct originals/class: 4,000 training, 500 validation and 500 test. For all 345 labels those are 1,380,000 / 172,500 / 172,500 originals.

Source checks use generation, byte count and MD5. The in-memory sample tracks conflicts only for retained IDs. Preparation uses one temporary SQLite index for retained candidates; conflicts are quarantined rather than relabeled. It writes directly to prepared shards and removes its temporary index. Candidates stay available for re-preparation. Historical generated folders are not automatically deleted.

Optional drawing exclusions go in `<data-root>/<profile>/excluded-ids.txt`, one ID per line. Legacy explicit exclusions are adopted when no text file exists. No review approval is required.

If preparation reports a shortage, explicitly enlarge the affected reserve, then prepare again:

```powershell
.\guesser-data.ps1 download --class "cat" --candidates 6500
.\guesser-data.ps1 prepare
```

See [the runbook](RUNBOOK.md) for transfer, loading and preprocessing examples.

## Small examples and supporting commands

```powershell
.\guesser-data.ps1 example        # one synthetic class; offline; separate example directory
.\guesser-data.ps1 probe          # explicit small real-source ranges; separate probe directory
```

Examples/probes default to the smoke profile (16/2/2 originals/class), are marked nonproduction, and do not establish recognition accuracy or production throughput. Prefix probes do not verify a whole source checksum. There is no global download budget.

Other commands: `preflight`, `status`, `inventory`, and `audit`. Every command supports `--help`, `--data-root`, `--profile` and `--json`. Download also supports repeatable `--class`, `--candidates` and `--concurrency`. Old `scan`, `freeze`, `qa` and `validate` commands show replacement hints. Normal output is readable text; JSON is optional.

## Images and model handoff

```python
from guesser_data import IndexedDrawings
from guesser_data import preprocess

with IndexedDrawings("prepared", "train") as drawings:
    sample = drawings.training_image(0, epoch=0)  # foreground is the default
    # sample['image']: float32 [3,224,224] when status == 'ok'
    # sample['class_id']: separate training target
```

Use `candidate="edges"` to toggle edge preprocessing. Keep the same choice across a model's training, validation, test and inference. Both modes fit/pad the current visible shape to 224x224 and normalize by mean/std 0.5; do not normalize twice. Timestamps create partial images; they are not direct ViT input features. Training views are 20% complete and otherwise use an elapsed-time cut in 10%-90%. Evaluation emits ten fixed 10%-100% stages, including blank, uncertain and unchanged outcomes. Crop bounds never use future points.

`dataset-summary.json` records source identity, seed, ordered labels, counts, preparation statistics and data hashes. It does not fingerprint source code or documentation. Export audits the data once, then separates training/validation from held-out test data. Changing prepared records requires preparation again; editing a README does not invalidate the dataset. Existing valid prepared data can receive the new summary during an audit without downloading again.

The data project uses Python 3.13. The relocated evaluation/notebook project uses Python 3.12 with its own uv lock; this change does not unify those environments or implement training/batching.

## Development

Follow the repository's concise Python guidelines. Use Ruff for formatting/lint and Pyright for types. Data tests live in `tests/`; model evaluation belongs in `../evaluation/`. Historical reports in `reports/` describe earlier workflows, not proof that the current code ran at full source scale.

Quick, Draw! is attributed to Google Creative Lab under CC BY 4.0. [Official format and source](https://github.com/googlecreativelab/quickdraw-dataset). AtyPict is outside this Guesser pipeline.
