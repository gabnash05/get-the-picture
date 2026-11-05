# Guesser evaluation workspace

This Python/Jupyter workspace supports the project's evaluation and inference work: auditing held-out inputs, evaluating frozen model checkpoints, measuring latency, and preparing the live inference interface. The environment and its smoke-check notebook are set up; the evaluator, serving API, model weights, and performance results are future work.

## What this workspace is for

- **Available now:** reproducible Python/Jupyter environment, source package scaffold, and `00_environment_check.ipynb` to verify the interpreter and scientific/image imports.
- **Planned use cases:** audit held-out drawing splits and rendered inputs; compare stage-wise recognition metrics for frozen checkpoints; inspect errors/calibration; measure snapshot-to-result latency; and connect a selected checkpoint to the inference API.
- **Not included yet:** Quick, Draw! data, model checkpoints, the evaluator, an inference service, or model results. Do not report the smoke notebook as an evaluation.

## Supported environment

- Python **3.12.16**, pinned in `.python-version` and constrained in `pyproject.toml`. This follows the Guesser plan's supported range and is a safer shared base for the planned ML stack.
- Target: 64-bit Windows and Linux. The committed `uv.lock` includes platform-specific wheel selections for both, and Windows resolution passed a uv dry run from Linux; a live Windows notebook run remains to be verified.
- Base Jupyter/scientific dependencies install by default. The optional `inference` extra adds the planned PyTorch 2.7.1 / torchvision 0.22.1 pair, timm, OpenCV, and FastAPI dependencies.
- GPU drivers are not in the lockfile. CUDA availability and performance depend on each machine; no Linux-only PyTorch index is configured.

## Prerequisites and setup

Install `uv` and Git. From the repository root, run the same commands in PowerShell or a Linux shell:

```sh
uv sync --project research/guesser-evaluation --locked
```

`uv` selects Python 3.12.16 from `.python-version` (downloading it if needed) and creates `research/guesser-evaluation/.venv`. No Pipenv, manual virtualenv activation, `.env`, or `PYTHONPATH` setting is needed; the workspace package is installed into the environment.

To add the model/API packages when that work begins:

```sh
uv sync --project research/guesser-evaluation --locked --extra inference
```

The inference extra downloads large PyTorch wheels. Confirm `torch.cuda.is_available()` on the target machine before relying on GPU inference; CPU environment checks still work if CUDA is unavailable.

## Configure notebook collaboration tools

Run these once **in every clone**, from the repository root, after `uv sync`:

```sh
uv run --project research/guesser-evaluation pre-commit install --config research/guesser-evaluation/.pre-commit-config.yaml
uv run --project research/guesser-evaluation nbdime config-git --enable
uv run --project research/guesser-evaluation nbstripout --install
```

What each step does:

- `pre-commit install` adds a local Git commit hook. The scoped `nbstripout` hook strips notebook outputs and execution metadata as a final check before commit.
- `nbdime config-git --enable` registers notebook-aware diff/merge drivers. The root `.gitattributes` contains the shared notebook driver rules.
- `nbstripout --install` adds a local Git clean filter. Notebook outputs are stripped from the staged version when you run `git add`, before the commit hook. This avoids committing bulky execution output and reduces output-only diffs.

The hook/filter and driver registrations live in `.git` configuration and are **not shared** with a clone. Each collaborator runs the commands above locally; the generated interpreter path is specific to that clone and OS, while `pyproject.toml`, `uv.lock`, and `.gitattributes` stay portable. The pre-commit hook is a second safety net. If it changes a notebook already staged, stage that notebook again before retrying the commit.

In a clone with the clean filter enabled, Git uses nbstripout's stripped text view for notebook diffs, while the configured nbdime merge driver handles notebook conflicts. Check the local setup with:

```sh
uv run --project research/guesser-evaluation nbstripout --status
git check-attr -a -- research/guesser-evaluation/notebooks/00_environment_check.ipynb
```

## Start JupyterLab

From the repository root:

```sh
uv run --project research/guesser-evaluation jupyter lab research/guesser-evaluation/notebooks
```

JupyterLab uses the project's Python kernel. Open `00_environment_check.ipynb` and run all cells to check Python, package imports, and a small image operation. It reports the current OS and interpreter so collaborators can confirm which environment they launched.

Useful launch options (append them before the notebook directory):

```sh
# Use another port if 8888 is busy
uv run --project research/guesser-evaluation jupyter lab --port=8890 research/guesser-evaluation/notebooks

# Do not open a browser automatically (for remote/headless use)
uv run --project research/guesser-evaluation jupyter lab --no-browser research/guesser-evaluation/notebooks

# Bind to all interfaces only when remote access is required
uv run --project research/guesser-evaluation jupyter lab --ip=0.0.0.0 research/guesser-evaluation/notebooks
```

Binding to `0.0.0.0` can expose the notebook server to other devices on the network. Use it only on a trusted network and keep Jupyter's token/password protection enabled.

If using a Jupyter server launched outside this environment, register the kernel once:

```sh
uv run --project research/guesser-evaluation python -m ipykernel install --user --name mtmai-guesser-evaluation --display-name "Python (MTMAI Guesser Evaluation)"
```

Then select **Python (MTMAI Guesser Evaluation)** in the notebook's kernel menu. If it is missing, repeat the registration command after syncing the environment.

## Notebook workflow and merge conflicts

Keep reusable Python code in `src/guesser_evaluation/`; use notebooks for imports/function calls, analysis, plots, and experiment records. The environment-check notebook demonstrates authoring with `%%writefile`: use its `module_source_path('module.py')` helper to target another module under the package root, then invalidate import caches and import/call it in a later cell. New subpackages also need `__init__.py`. Treat each `%%writefile` cell as the source of truth for its generated `.py` module: make all code changes to that module in the notebook cell, then run it to regenerate the file. Direct edits to a generated `.py` are temporary and will be overwritten the next time its writer cell runs. Give every additional module its own writer cell; the environment-check pair has a synchronization test. Commit the notebook and each resulting `.py` file as separate single-file commits so tests and terminal runs work without executing the notebook. `%autoreload 2` may help during interactive iteration. Do not keep reusable application logic only in ordinary notebook cells. Commit code/configuration and reviewed report summaries, not raw dataset files, checkpoints, or large run artifacts. The `.gitignore` covers local data, model, run, and output directories.

Before editing notebooks, create a small feature branch and avoid having two people edit the same notebook cells at once:

```sh
git switch -c feature/evaluation-notebook
```

When a notebook merge conflict remains after `git merge` or `git pull`, do **not** resolve the `.ipynb` JSON or conflict markers by hand. From the repository root, run:

```sh
uv run --project research/guesser-evaluation nbdime mergetool
```

Nbdime opens a three-way notebook merge view so you can compare the base, local, and incoming notebook cells. Review the merged notebook, save it, then stage the resolved file and continue the merge:

```sh
git status --short
git add research/guesser-evaluation/notebooks/<resolved-notebook>.ipynb
git commit
```

The nbdime merge driver handles notebook structure; `nbstripout` removes irrelevant output/metadata churn. These tools reduce noisy diffs and make cell-level conflict resolution practical, but they cannot eliminate conflicts when both branches change the same cell differently. If `nbdime mergetool` reports no files need merging, confirm the conflict is in a notebook and that the clone setup commands above completed.

## Add dependencies and run checks

Do not install packages with bare `pip`. Add a dependency to the appropriate group or optional extra in `pyproject.toml`, regenerate the lock, then sync:

```sh
uv lock --project research/guesser-evaluation
uv sync --project research/guesser-evaluation --locked
```

Run the current environment checks from the repository root:

```sh
uv run --project research/guesser-evaluation python -m pytest
uv run --project research/guesser-evaluation ruff check research/guesser-evaluation/src research/guesser-evaluation/tests
```

Commit the updated `uv.lock` with dependency changes so Windows and Linux collaborators resolve the same versions.
