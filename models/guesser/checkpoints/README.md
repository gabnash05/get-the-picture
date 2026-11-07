# Guesser checkpoints

Local training artifacts live here and are **ignored by Git** (only this README and `.gitignore` are tracked).

Typical contents after A/B training:

- `A_complete_only/` and `B_partial/` — Lightning `weights/*.ckpt`, CSV `logs/`, `checkpoint-selection.json`
- `ab_comparison/` — lightweight A vs B summary from `python -m training.compare_ab`
- `train-summary.json` — combined run metadata when training finishes

Do not commit `.ckpt` files or large logs. For handoff: push the training **code** and lockfile; transfer a small proof zip (selection JSON + `ab_comparison/`) separately if needed. Production retraining on another machine should point `train.py` at that host's prepared data via `--prepared-dir`, not at these small-run weights unless Validation explicitly wants them.
