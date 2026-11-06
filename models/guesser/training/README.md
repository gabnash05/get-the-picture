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

## Required libraries

Use timm for the pretrained ViT-Tiny and its 345-class head; Lightning Trainer/Module/DataModule and callbacks for the training loop, device/precision handling, resume, checkpoint selection and logs; PyTorch Dataset/DataLoader for batches; torchvision v2 for ordinary augmentation; PyTorch loss/optimizer/schedulers and TorchMetrics for standard learning operations and scores. Keep custom code to data adaptation and the experiment protocol.

See the [library guide](../LIBRARIES.md) and [implementation rules](../AGENTS.md).
