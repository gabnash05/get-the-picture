# Models

Keep Guesser and Referee work separate. The Guesser data package is implemented; training/inference remain placeholders, while Guesser evaluation now contains a separate uv/Jupyter scaffold.

```text
models/
  guesser/
    data/          # Data tools, uv project and setup instructions
    training/      # Training code
    inference/     # Prediction service and model loading
    evaluation/    # Model validation, preprocessing pilot and benchmarks
    checkpoints/   # Local model weights; ignored by Git
  referee/
    training/
    inference/
    evaluation/
    checkpoints/   # Local model weights; ignored by Git
```

Start with the [Guesser data setup](guesser/data/README.md) and [model teammate runbook](guesser/data/RUNBOOK.md). Its Python dependencies are managed by uv in `guesser/data/pyproject.toml` and `guesser/data/uv.lock`. Run its commands from `models/guesser/data/`; the command name remains `guesser-data`.

Data-pipeline checks belong in `guesser/data/tests/`. Model experiments and accuracy evaluation belong in `guesser/evaluation/`. The approved design remains in [docs/guesser](../docs/guesser/README.md). Downloaded data, local environments and caches stay under the data package's ignored `.local/` and `.venv/` directories (E: is the preferred local drive; explicit data paths may use any drive).
