# Guesser training

Lightning adapters for fine-tuning the agreed ViT-Tiny backbone on prepared Guesser data.

## Role split (current)

- **This machine / small-dataset owner:** finish clean A/B on the **small** prepared set, compare validation curves, package the training codebase + recipe for handoff.
- **Teammate (faster laptop):** reuse this code later on **medium/production** prepared data via `--prepared-dir` (do not change splits or held-out test).

Scripts:

- `dataset.py`: `GuesserDataset` / `GuesserDataModule` over `IndexedDrawings`
  - Run **A** (`complete_only=True`): full originals
  - Run **B** (`complete_only=False`): `training_image` partial recipe
  - Validation during training uses complete originals (ten-stage / held-out eval stays with Validation)
- `module.py`: timm ViT-Tiny + dual-LR AdamW + warmup/cosine
- `train.py`: matched-budget A/B training, checkpoints, selection JSON
- `smoke_test.py`: one-batch GPU sanity for A and B
- `compare_ab.py`: lightweight A vs B CSV/metrics comparison + SVG plots

Use the sibling [data package](../data/README.md) for prepared data and shared preprocessing. Put weights under [`../checkpoints/`](../checkpoints/).

## Smoke check

From `models/guesser/` with the model venv active:

```powershell
.\.venv\Scripts\python.exe -m training.smoke_test
```

## Train A and B (equal budget)

Defaults match the model plan: seed `198173`, effective batch 32 (`8 × accumulate 4`), up to 6 epochs, early stopping patience 2, FP32, validation-only checkpointing under `../checkpoints/`.

```powershell
# Dry run (1 epoch, a few batches)
.\.venv\Scripts\python.exe -m training.train --fast

# Full matched runs on the small prepared set (2 workers prefetch renders)
.\.venv\Scripts\python.exe -m training.train --run both --num-workers 2

# One run at a time
.\.venv\Scripts\python.exe -m training.train --run a --num-workers 2
.\.venv\Scripts\python.exe -m training.train --run b --num-workers 2

# Teammate later: point at a larger prepared tree (same flags otherwise)
.\.venv\Scripts\python.exe -m training.train --run both --num-workers 4 --prepared-dir data\.local\data\production\prepared
```

Artifacts per run: `checkpoints/A_complete_only/` and `checkpoints/B_partial/` (weights, CSV logs, `checkpoint-selection.json`). Do not use held-out test for tuning.

## Pause and resume

`last.ckpt` is refreshed every 1000 train steps; the best `val_acc` checkpoint is saved after each validation epoch (separate callbacks). Resume with the same flags plus `--resume`:

```powershell
.\.venv\Scripts\python.exe -m training.train --run a --num-workers 2 --resume
.\.venv\Scripts\python.exe -m training.train --run b --num-workers 2 --resume
```

## Compare A vs B (after both runs finish)

```powershell
.\.venv\Scripts\python.exe -m training.compare_ab
```

Writes `checkpoints/ab_comparison/`:

- `comparison.md` / `comparison-summary.json` — best `val_acc`, epochs, paths
- `val_acc.svg` / `val_loss.svg` — overlaid A vs B curves
- per-run SVGs

This is a **small-dataset training-validation** comparison, not the final ten-stage held-out report.

## Handoff checklist for the training teammate

Send / commit (weights stay gitignored — transfer separately if needed):

1. `training/` package (`dataset.py`, `module.py`, `train.py`, `compare_ab.py`, `smoke_test.py`, README)
2. `pyproject.toml` + `uv.lock` (CUDA index already set for Windows cu126; teammate should re-lock for their GPU if needed)
3. Small-run `checkpoint-selection.json` files (recipe + `labels_sha256`) and `ab_comparison/`
4. Note the exact command used for small A/B, and that production only needs `--prepared-dir` (+ maybe more workers)

## Required libraries

Use timm for the pretrained ViT-Tiny and its 345-class head; Lightning Trainer/Module/DataModule and callbacks for the training loop, device/precision handling, resume, checkpoint selection and logs; PyTorch Dataset/DataLoader for batches; torchvision v2 for ordinary augmentation; PyTorch loss/optimizer/schedulers and TorchMetrics for standard learning operations and scores. Keep custom code to data adaptation and the experiment protocol.

See the [library guide](../LIBRARIES.md) and [implementation rules](../AGENTS.md).
