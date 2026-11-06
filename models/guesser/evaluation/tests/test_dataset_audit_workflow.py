"""Tests for notebook-driven dataset-audit workflow helpers."""

import ast
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from guesser_evaluation import dataset_audit_workflow
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
    # Data imports may appear in the subprocess query, never in this kernel's AST.
    assert not any(
        isinstance(node, ast.ImportFrom) and (node.module or "").startswith("guesser_data")
        for node in ast.walk(ast.parse(code))
    )
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
    with patch.object(dataset_audit_workflow, "data_profile", return_value={}):
        assert audit_production_dataset(tmp_path) is None


@pytest.mark.parametrize("profile", ["production", "medium", "small"])
def test_profile_audit_uses_data_contract(tmp_path: Path, profile: str) -> None:
    """Use discovered counts rather than a production-only split contract."""
    (tmp_path / "prepared").mkdir()
    (tmp_path / "dataset-summary.json").write_text(json.dumps({"profile": profile}))
    contract = {"class_count": 345, "counts": {"train": 7, "validation": 2, "test": 1}}
    with (
        patch.object(dataset_audit_workflow, "data_profile", return_value=contract),
        patch("guesser_evaluation.dataset_audit.audit_prepared_dataset") as auditor,
    ):
        dataset_audit_workflow.audit_dataset(tmp_path, profile=profile)
    auditor.assert_called_once_with(
        tmp_path / "prepared", expected_class_count=345, expected_per_class=contract["counts"]
    )


def test_profile_audit_rejects_mismatched_dataset(tmp_path: Path) -> None:
    """Never audit another profile under the selected profile's expectations."""
    (tmp_path / "prepared").mkdir()
    (tmp_path / "dataset-summary.json").write_text(json.dumps({"profile": "production"}))
    with (
        patch.object(dataset_audit_workflow, "data_profile", return_value={}),
        pytest.raises(ValueError, match="profile"),
    ):
        dataset_audit_workflow.audit_dataset(tmp_path, profile="small")


def test_pipeline_uses_discovered_defaults_and_resolves_output_paths() -> None:
    """Delegate defaults to the data environment and anchor relative overrides."""
    workspace = Path(__file__).parents[1]
    notebook = json.loads(
        (workspace / "notebooks" / "01_dataset_pipeline.ipynb").read_text(encoding="utf-8")
    )
    defaults = {
        "profile": "medium",
        "data_root": "/fixture/data",
        "concurrency": 2,
        "profiles": {"medium": {"candidates": 2200}},
        "trainable_profiles": ["medium"],
        "download_methods": {"medium": "prefix"},
        "seed": 198173,
        "preprocessing": {},
    }
    namespace = {}

    def execute_cell(index: int) -> None:
        """Exercise trusted repository cells with subprocess side effects mocked."""
        exec("".join(notebook["cells"][index]["source"]), namespace)  # noqa: S102

    # Discovery is read-only; production stages are replaced by captured subprocess calls.
    with patch("subprocess.run", return_value=SimpleNamespace(stdout=json.dumps(defaults))):
        execute_cell(1)
    execute_cell(3)
    assert namespace["PROFILE"] == "medium"
    assert namespace["CONCURRENCY"] is None
    assert namespace["CANDIDATE_RESERVE"] is None
    namespace.update(DATA_ROOT="custom-data", EXPORT_OUTPUT_DIR="custom-exports")
    execute_cell(5)
    with patch("subprocess.run") as run:
        execute_cell(6)
        namespace.update(RUN_PIPELINE=True, INCLUDE_PREVIEW=True)
        execute_cell(7)
    root = namespace["REPOSITORY_ROOT"]
    assert namespace["EXPORT_DIRECTORY"] == root / "custom-exports"
    commands = [call.args[0] for call in run.call_args_list]
    assert all(str(root / "custom-data") in command for command in commands)
    export = next(command for command in commands if "export" in command)
    assert export[-2:] == ["--output-dir", str(root / "custom-exports")]
    download = next(command for command in commands if "download" in command)
    assert "--concurrency" not in download
    assert "--candidates" not in download
