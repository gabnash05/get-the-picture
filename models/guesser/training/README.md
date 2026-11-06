# Guesser training

Lightning adapters for fine-tuning the agreed ViT-Tiny backbone on prepared Guesser data.

- `dataset.py`: `GuesserDataset` / `GuesserDataModule` over `IndexedDrawings`
  - Run **A** (`complete_only=True`): full originals
  - Run **B** (`complete_only=False`): `training_image` partial recipe
  - Validation always uses complete originals (full stage-wise eval stays with Validation)
- `module.py`: timm ViT-Tiny + dual-LR AdamW + warmup/cosine
- `smoke_test.py`: one-batch GPU sanity for A and B

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

# If VRAM allows, larger physical batches can reduce step overhead (keep effective batch 32)
.\.venv\Scripts\python.exe -m training.train --run both --num-workers 2 --batch-size 16 --accumulate-grad-batches 2

# One run at a time
.\.venv\Scripts\python.exe -m training.train --run a
.\.venv\Scripts\python.exe -m training.train --run b
```

Artifacts per run: `checkpoints/A_complete_only/` and `checkpoints/B_partial/` (weights, CSV logs, `checkpoint-selection.json`). Do not use held-out test for tuning.

## Pause and resume

`last.ckpt` is refreshed every 1000 train steps and at epoch end. Tonight you can stop after a save; tomorrow resume with the same flags plus `--resume`:

```powershell
# Prefer letting the current epoch finish, then Ctrl+C
# Or Ctrl+C after you see a checkpoint write under checkpoints/*/weights/

.\.venv\Scripts\python.exe -m training.train --run a --num-workers 2 --resume
.\.venv\Scripts\python.exe -m training.train --run b --num-workers 2 --resume
```

Use the same `--batch-size`, `--accumulate-grad-batches`, `--max-epochs`, and `--prepared-dir` as the original run.

## Required libraries

Use timm for the pretrained ViT-Tiny and its 345-class head; Lightning Trainer/Module/DataModule and callbacks for the training loop, device/precision handling, resume, checkpoint selection and logs; PyTorch Dataset/DataLoader for batches; torchvision v2 for ordinary augmentation; PyTorch loss/optimizer/schedulers and TorchMetrics for standard learning operations and scores. Keep custom code to data adaptation and the experiment protocol.

See the [library guide](../LIBRARIES.md) and [implementation rules](../AGENTS.md).
