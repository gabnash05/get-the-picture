"""Tests for notebook-driven dataset-audit workflow helpers."""

import json
from pathlib import Path

from guesser_evaluation.dataset_audit_workflow import audit_production_dataset
from guesser_evaluation.notebook_tools import module_source_path


def test_notebook_source_cell_matches_generated_workflow_module() -> None:
    """Keep notebook-authored workflow logic synchronized with its importable module."""
    workspace = Path(__file__).parents[1]
    notebook = json.loads(
        (workspace / "notebooks" / "02_dataset_audit.ipynb").read_text(encoding="utf-8")
    )
    # The writer body is the canonical code users regenerate from Jupyter.
    source_cell = next(
        cell
        for cell in notebook["cells"]
        if cell["cell_type"] == "code" and cell["source"][0].startswith("%%writefile ")
    )
    module = module_source_path("dataset_audit_workflow.py", start=workspace)

    assert "".join(source_cell["source"][1:]) == module.read_text(encoding="utf-8")


def test_pipeline_notebook_reuses_cli_and_documents_options() -> None:
    """Keep pipeline orchestration thin, explicit, and safe to open or run all."""
    workspace = Path(__file__).parents[1]
    notebook = json.loads(
        (workspace / "notebooks" / "01_dataset_pipeline.ipynb").read_text(encoding="utf-8")
    )
    markdown = "\n".join(
        "".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "markdown"
    )
    code = "\n".join(
        "".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"
    )

    # The evaluation kernel delegates data work to the existing public CLI.
    assert '"guesser-data"' in code
    assert all(f'"{stage}"' in code for stage in ("download", "prepare", "preview", "export"))
    assert "from guesser_data" not in code
    # Production work must require an explicit opt-in, and its controls stay documented.
    assert "RUN_PIPELINE = False" in code
    assert "## Options" in markdown
    assert "--concurrency" in markdown
    assert "trainer-production.zip" in markdown


def test_pipeline_setup_cell_syncs_from_repo_root_only_when_enabled() -> None:
    """Keep environment setup explicit and anchored to the repository root."""
    workspace = Path(__file__).parents[1]
    notebook = json.loads(
        (workspace / "notebooks" / "01_dataset_pipeline.ipynb").read_text(encoding="utf-8")
    )
    setup_cell = notebook["cells"][1]
    setup_source = "".join(setup_cell["source"])

    # The sync cell follows its setup instructions and cannot run during Run All by default.
    assert setup_cell["cell_type"] == "code"
    assert "SYNC_DATA_ENVIRONMENT = False" in setup_source
    assert "if SYNC_DATA_ENVIRONMENT:" in setup_source
    assert '"sync", "--project", "models/guesser/data", "--frozen"' in setup_source
    assert "cwd=REPOSITORY_ROOT" in setup_source


def test_workflow_waits_cleanly_until_prepared_data_exists(tmp_path: Path) -> None:
    """Allow the notebook to run while the production download is still underway."""
    # Missing prepared files should produce a pending state rather than a false pass.
    assert audit_production_dataset(tmp_path) is None
