# Guesser library choices

Use existing deep learning libraries for standard work. This supplements the reviewed Guesser plan and is the current implementation guidance for library selection and uv setup.

## Current implementation status

The completed data package already uses NumPy for array operations, Pillow for drawing/resizing, OpenCV for edge detection, PyArrow for Parquet, SQLite for identity/conflict indexing, and checksum libraries. Its record reader handles the project's seekable JSONL format; it is not a replacement for PyTorch's batching and worker system.

Training adapters live under [`training/`](training/README.md) (LightningModule/DataModule, A/B `train.py`, smoke and `compare_ab`). The model uv project at `models/guesser/` declares `torch`, `torchvision`, `timm`, `lightning`, `torchmetrics` and `safetensors` in `pyproject.toml` / `uv.lock`. Choose the CUDA/CPU index for the actual training host before `uv sync`. Evaluation metrics beyond training-time validation and the inference service remain Validation/Inference owner work. Trained weights are not committed.

## Required library map

| Work | Use | Project code that remains |
|---|---|---|
| Pretrained vision transformer and 345-class head | [timm create_model](https://huggingface.co/docs/timm/reference/models) | Select the checkpoint and pass `num_classes=345`. |
| Training and validation loop, device handling and mixed precision | [Lightning Trainer](https://lightning.ai/docs/pytorch/stable/core-api/trainer) | A small LightningModule defines the batch, loss and metrics; a DataModule supplies prepared data. |
| Best-model saves, early stopping, resume and logs | Lightning ModelCheckpoint, EarlyStopping, LearningRateMonitor and CSVLogger | Choose the validation score, patience, paths and equal A/B update budget. |
| Data batches, shuffling, worker processes and prefetch | [PyTorch Dataset/DataLoader](https://docs.pytorch.org/docs/stable/data.html) | Adapt IndexedDrawings and timestamp views; propagate epoch/seed deterministically to workers. |
| Loss, optimizer and scheduling | PyTorch CrossEntropyLoss, AdamW and built-in LR schedulers | Supply the agreed hyperparameters; do not implement gradient descent or scheduler formulas. |
| Ordinary image augmentation | [torchvision transforms v2](https://docs.pytorch.org/vision/stable/transforms.html) | Choose modest training-only rotation/translation/scale consistent with the data plan. |
| Top-1/top-3, F1, confusion and calibration error | [TorchMetrics classification metrics](https://lightning.ai/docs/torchmetrics/stable/classification/accuracy.html) | Run the approved per-stage protocol and keep explicit blank/pass counts. |
| Confidence calibration | TorchMetrics for [calibration error](https://lightning.ai/docs/torchmetrics/stable/classification/calibration_error.html), PyTorch loss/optimizer primitives or a suitable maintained calibration utility for fitting | Fit on validation only and record the temperature/pass policy. Measuring calibration error does not itself calibrate a model. |
| Model prediction | PyTorch eval/inference_mode and tensor softmax/topk | Apply the chosen shared preprocessor, label registry and game policy. |
| Weight I/O | Lightning checkpoints for training resume; timm/safetensors for inference weights | Bundle registry/preprocessor hashes and rebuild the same architecture. |
| HTTP service and request checks | [FastAPI/Pydantic](https://fastapi.tiangolo.com/tutorial/body/) and Uvicorn | Define the game's request/result/version contract and bounded resident-model worker. |
| Package management | [uv](https://docs.astral.sh/uv/guides/integration/pytorch/) | Declare dependencies, select the machine's supported PyTorch backend, and commit the lock. |

Do not combine multiple training engines for the same run. The selected combination is timm for the model plus Lightning for training. Hugging Face Trainer/Accelerate, fastai or another engine are not additional requirements alongside it.

## Backbone and preprocessing

The starting checkpoint remains [vit_tiny_patch16_224.augreg_in21k_ft_in1k](https://huggingface.co/timm/vit_tiny_patch16_224.augreg_in21k_ft_in1k). It is an existing image classifier; the group adapts it to sketches instead of constructing a transformer.

```python
import timm

model = timm.create_model(
    "vit_tiny_patch16_224.augreg_in21k_ft_in1k",
    pretrained=True,
    num_classes=345,
)
```

This is an implementation reference, not code executed during this review. `pretrained=True` downloads weights when first used, so run it only as part of the model owner's setup, with the cache on E:.

Use timm's pretrained metadata to check expected image size/normalization. Keep the project's shared current-prefix Foreground/Edges and fit/pad transform rather than blindly applying a model's generic center-crop transform. Existing prepared views are already float32 [3,224,224] and normalized; converting them with `torch.from_numpy` must not normalize them a second time. Standard training augmentation should use torchvision APIs, be seeded, and be absent from validation/live inference.

The only custom neural wrapper should be a small LightningModule around the existing timm model. The group should not implement transformer blocks, a complete training engine, mixed-precision scaling, gradient accumulation, checkpoint recovery, standard metrics or an HTTP framework.

## Work split

- Data owner: retain the existing CPU-only package and identity/split/preprocessing contract. Reuse its renderer and record reader in the model adapter.
- Model owner: use timm + Lightning + PyTorch DataLoader + torchvision; run the matched-budget A/B experiment with framework callbacks and logs.
- Validation/inference owner: use TorchMetrics and the fixed timestamp-stage protocol; keep test custody and build the FastAPI/Pydantic resident-model service using PyTorch inference APIs.

Project-specific code remains necessary for ordered timestamp cuts, exact sampling/conflict rules, early-recognition aggregation and game checkpoint/version policy. Implement those as small adapters around the libraries. A generic random split or automatic image crop must not replace an agreed rule and change the experiment.

## uv setup for the model project

Keep `data/` independent so data preparation never requires a large torch/GPU install. The model uv project already lives at `models/guesser/` with an editable workspace dependency on `./data`. Teammates should sync that project rather than re-running `uv init`:

```powershell
# Run in models/guesser/; keep environment and cache here.
$env:UV_CACHE_DIR = Join-Path $PWD '.local/cache/uv'
$env:TEMP = Join-Path $PWD '.local/tmp'
$env:TMP = $env:TEMP
$env:HF_HOME = Join-Path $PWD '.local/cache/huggingface'
$env:TORCH_HOME = Join-Path $PWD '.local/cache/torch'
$env:UV_PYTHON_DOWNLOADS = 'never'
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
uv sync --frozen
```

If the locked CUDA index does not match the host (for example a different driver or Linux), follow the official [uv PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/), adjust `[[tool.uv.index]]` / `[tool.uv.sources]` for torch/torchvision, then re-lock and sync. Keep torch and torchvision compatible. A gaming laptop description alone does not identify the correct wheel.

Required model packages: `torch`, `torchvision`, `timm`, `lightning`, `torchmetrics`, `safetensors`. Service dependencies (`fastapi`, `pydantic`, `uvicorn`) remain for the inference owner. Commit `pyproject.toml` and `uv.lock`; teammates use `uv sync --frozen` when the lock matches their platform.

The evaluation scaffold in `evaluation/` keeps its separate Python 3.12 lock. Data remains Python 3.13. Those environments are not interchangeable.
