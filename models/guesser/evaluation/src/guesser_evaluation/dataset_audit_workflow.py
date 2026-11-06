"""Notebook helpers for locating, auditing, and plotting Guesser data."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


def data_profile(profile: str | None = None) -> dict[str, Any]:
    """Read the selected profile contract in the data project's own environment."""
    from .notebook_tools import module_source_path

    source_path = module_source_path("dataset_audit_workflow.py")
    data_project = source_path.parents[2].parent / "data"
    # Query settings without syncing or importing Python 3.13 code into this kernel.
    query = """
import json, sys
from guesser_data.cli import parser
from guesser_data.settings import PACKAGE_ROOT, Settings
defaults = parser().parse_args(["download"])
settings = Settings(profile=sys.argv[1] or defaults.profile)
if not settings.is_trainable:
    raise ValueError("Audit requires a trainable profile, not smoke")
print(json.dumps({
    "profile": settings.profile, "data_root": str(settings.base),
    "counts": {split: settings.spec[split] for split in ("train", "validation", "test")},
    "class_count": len((PACKAGE_ROOT / "src/resources/categories.txt").read_text().splitlines()),
    "sampling_method": settings.download_method,
}))
"""
    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(data_project),
            "--frozen",
            "--no-sync",
            "python",
            "-c",
            query,
            "" if profile is None else profile,
        ],
        cwd=data_project.parents[2],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def profile_data_root(profile: str | None = None) -> Path:
    """Resolve a profile directory, preserving the legacy environment override."""
    contract = data_profile(profile)
    return Path(os.environ.get("MTMAI_GUESSER_DATA_ROOT", contract["data_root"])).expanduser()


def production_data_root() -> Path:
    """Keep the original production-only path helper compatible."""
    return profile_data_root("production")


def audit_dataset(
    data_root: str | Path | None = None, *, profile: str | None = None
) -> dict[str, Any] | None:
    """Audit a selected training profile, returning None while preparation is pending."""
    from .dataset_audit import audit_prepared_dataset

    contract = data_profile(profile)
    selected = contract["profile"] if profile is None else profile
    # Explicit paths and the legacy environment variable name a profile directory.
    configured = (
        data_root
        if data_root is not None
        else os.environ.get("MTMAI_GUESSER_DATA_ROOT", contract["data_root"])
    )
    root = Path(configured).expanduser()
    prepared_path = root / "prepared"
    # A missing folder means preparation is pending, not that the audit passed.
    if not prepared_path.is_dir():
        return None
    summary = json.loads((root / "dataset-summary.json").read_text(encoding="utf-8"))
    if summary.get("profile") != selected:
        raise ValueError(f"Dataset profile does not match selected profile {selected!r}")
    return audit_prepared_dataset(
        prepared_path,
        # Counts and registry size come from the data source, not duplicated constants.
        expected_class_count=contract["class_count"],
        expected_per_class=contract["counts"],
    )


def audit_production_dataset(data_root: str | Path | None = None) -> dict[str, Any] | None:
    """Preserve the existing production-only public entry point."""
    return audit_dataset(data_root, profile="production")


def plot_class_balance(report: dict[str, Any]):
    """Return per-split totals and a class-count figure from a passed audit."""
    import matplotlib.pyplot as plt
    import pandas as pd

    counts = pd.DataFrame(report["counts_by_class"])
    # Sum the same audited rows shown in the plot for a quick total check.
    totals = counts[["train", "validation", "test"]].sum()
    # Stack partitions so class balance can be compared without hiding any split.
    figure, axis = plt.subplots(figsize=(18, 5))
    counts.set_index("source_name")[["train", "validation", "test"]].plot(
        kind="bar", stacked=True, width=0.9, ax=axis
    )
    axis.set_title("Original drawings by Quick, Draw! class and split")
    axis.set_xlabel("Class")
    axis.set_ylabel("Original drawings")
    figure.tight_layout()
    return totals, figure
