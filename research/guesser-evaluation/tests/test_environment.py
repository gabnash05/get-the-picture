"""Tests for the Guesser workspace environment and notebook source workflow."""

import json
import sys
from pathlib import Path

import guesser_evaluation
from guesser_evaluation.environment_check import collect_environment
from guesser_evaluation.notebook_tools import module_source_path


def test_workspace_uses_supported_python_minor() -> None:
    """Verify tests run with the Python minor version supported by the workspace."""
    assert sys.version_info[:2] == (3, 12)


def test_workspace_package_is_importable() -> None:
    """Confirm the src-layout package is installed in the active environment."""
    assert guesser_evaluation.__file__ is not None


def test_environment_check_runs_smoke_operations() -> None:
    """Exercise image and tabular operations without loading model or dataset files."""
    report = collect_environment()

    assert report["image_shape"] == (224, 224)
    assert report["dataframe_shape"] == (2, 1)


def test_notebook_writefile_cell_matches_terminal_module() -> None:
    """Keep the notebook writer cell and terminal-runnable module byte-for-byte aligned."""
    workspace = Path(__file__).parents[1]
    notebook = json.loads(
        (workspace / "notebooks" / "00_environment_check.ipynb").read_text(encoding="utf-8")
    )
    module = workspace / "src" / "guesser_evaluation" / "environment_check.py"
    writefile_cell = next(
        cell
        for cell in notebook["cells"]
        if cell["cell_type"] == "code" and cell["source"][0].startswith("%%writefile ")
    )

    assert "".join(writefile_cell["source"][1:]) == module.read_text(encoding="utf-8")


def test_notebook_source_path_helper_supports_additional_modules() -> None:
    """Resolve additional package modules from repository, workspace, or notebook roots."""
    workspace = Path(__file__).parents[1]
    expected = (workspace / "src" / "guesser_evaluation" / "analysis.py").resolve()

    for start in (workspace.parents[1], workspace, workspace / "notebooks"):
        assert module_source_path("analysis.py", start=start) == expected
