# Guesser model implementation rules

Follow the repository AGENTS.md and the current game contract. This file applies to the Guesser only.

## Reuse existing libraries

Use maintained library implementations for standard deep learning tasks. Start with the APIs in [LIBRARIES.md](LIBRARIES.md). Write only the small adapters needed to connect those APIs to this project's data and game rules.

- Create the pretrained transformer with `timm.create_model("vit_tiny_patch16_224.augreg_in21k_ft_in1k", pretrained=True, num_classes=345)`. Use timm's model loading and classifier replacement; do not implement transformer layers or attention.
- Use `lightning.pytorch.LightningModule`, `LightningDataModule`, and `Trainer` for model training, validation, device handling, precision, gradient accumulation and resume. Use Lightning `ModelCheckpoint`, `EarlyStopping`, `LearningRateMonitor` and `CSVLogger` rather than a custom training engine, checkpoint manager or logging framework.
- Use `torch.utils.data.Dataset` and `DataLoader` for model batches and workers. A thin adapter may wrap the existing `data/src/05-loader.py` record reader. Do not build another multiprocessing/batching/prefetch system.
- Use PyTorch's cross-entropy loss, AdamW, learning-rate schedulers and tensor operations for standard learning math. Use `torchvision.transforms.v2` for ordinary image augmentation. Preserve the shared Foreground/Edges preprocessing, causal current-prefix bounds and fit/pad convention; do not add a generic center crop or normalize twice.
- Use TorchMetrics for standard classification and calibration metrics, with explicit averaging and denominators. Keep the ten timestamp stages, blank/pass handling and original-grouped reporting as thin project-specific orchestration. Do not silently drop blank stages from the main recognition denominator.
- Use PyTorch `model.eval()` and `torch.inference_mode()` for inference, and existing timm/safetensors loading APIs for weights. Use FastAPI, Pydantic and Uvicorn for the service rather than implementing HTTP or schema validation.
- Reuse the existing NumPy, Pillow, OpenCV and PyArrow operations for the CPU-only data workflow. Keep timestamp cuts, deterministic identity-based sampling/splits, conflict handling, Foreground/Edges decisions and game checkpoint/version rules explicit; these are project requirements, not generic framework features.

## Dependencies and scope

Manage Python dependencies with uv and commit pyproject.toml/uv.lock together. The data package remains usable without PyTorch or a GPU. Model dependencies belong to the model owner's environment, with the correct PyTorch/torchvision backend chosen for the actual machine before locking and syncing. Keep generated data/caches ignored; default to the checkout's .local/ and allow explicit output paths on any drive. Put weights in ignored checkpoints/.

Training must read already prepared data; it must not trigger a production download automatically. Preserve all 345 labels, original-drawing split membership, the controlled complete-only versus partial-training experiment and held-out-test custody. Do not claim that a library is installed, a model is trained or a benchmark passed merely because this policy names it.
