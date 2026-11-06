"""Notebook helpers for locating, auditing, and plotting Guesser data."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def production_data_root() -> Path:
    """Resolve the default production data root or the portable override."""
    from .notebook_tools import module_source_path

    # Infer the sibling data project from this source file, not a machine-specific path.
    source_path = module_source_path("dataset_audit_workflow.py")
    default_root = source_path.parents[2].parent / "data" / ".local" / "data" / "production"
    # Let another clone or extracted package override the repository's local default.
    configured_root = os.environ.get("MTMAI_GUESSER_DATA_ROOT", str(default_root))
    return Path(configured_root).expanduser()


def audit_production_dataset(data_root: str | Path | None = None) -> dict[str, Any] | None:
    """Audit prepared production manifests, or return None until they exist."""
    from .dataset_audit import audit_prepared_dataset

    # Use the explicit argument when supplied; otherwise resolve the portable default.
    root = Path(data_root).expanduser() if data_root is not None else production_data_root()
    prepared_path = root / "prepared"
    # A missing folder means preparation is pending, not that the audit passed.
    if not prepared_path.is_dir():
        return None
    return audit_prepared_dataset(
        prepared_path,
        # Enforce the production label set and per-class split contract.
        expected_class_count=345,
        expected_per_class={"train": 4000, "validation": 500, "test": 500},
    )


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
