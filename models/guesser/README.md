# Guesser

- [data/](data/README.md): implemented numbered data stages and shared timed-image creation; Python 3.13/uv. Profiles: `production`, `medium`, `small` (plus non-trainable `smoke` examples).
- [training/](training/README.md): implemented Lightning + timm ViT-Tiny fine-tuning for matched A/B runs (`complete_only` vs partial). Point `--prepared-dir` at small/medium/production `prepared/` data. Weights stay under ignored `checkpoints/`.
- [inference/](inference/README.md): future prediction service and model loading.
- [evaluation/](evaluation/README.md): relocated Python 3.12/uv notebook and environment-check scaffold; stage-wise metrics and benchmarks remain future Validation work.
- `checkpoints/`: local weights, CSV logs, and A/B comparison artifacts; ignored by Git (transfer separately if needed).

Use the [library guide](LIBRARIES.md) and [implementation rules](AGENTS.md). Standard deep learning tasks should use maintained library APIs. No production-trained weights or inference service are shipped in Git.
