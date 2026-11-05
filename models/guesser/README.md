# Guesser

- [data/](data/README.md): implemented numbered data stages and shared timed-image creation; Python 3.13/uv.
- [training/](training/README.md): future model adaptation and PyTorch batching.
- [inference/](inference/README.md): future prediction service and model loading.
- [evaluation/](evaluation/README.md): relocated Python 3.12/uv notebook and environment-check scaffold; metrics and benchmarks remain future work.
- `checkpoints/`: local weights, ignored by Git.

Use the [library guide](LIBRARIES.md) and [implementation rules](AGENTS.md). Standard deep learning tasks should use maintained library APIs. No trained model, evaluator or inference service is supplied by the data refactor.
