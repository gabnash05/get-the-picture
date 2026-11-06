"""Tests for independent prepared-dataset manifest auditing."""

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from guesser_evaluation.dataset_audit import audit_prepared_dataset


def _write_fixture(root: Path, *, duplicate_id: bool = False) -> Path:
    """Create a tiny prepared-dataset layout with three split manifests."""
    prepared = root / "prepared"
    manifest_dir = prepared / "manifests"
    manifest_dir.mkdir(parents=True)
    # Two stable class IDs are enough to exercise ordering and class-count checks.
    labels = [
        {"class_id": 0, "source_name": "cat"},
        {"class_id": 1, "source_name": "dog"},
    ]
    (root / "labels.json").write_text(json.dumps(labels), encoding="utf-8")
    # The summary acts as an independent expected-count source for the auditor.
    counts = {str(class_id): {"train": 1, "validation": 1, "test": 1} for class_id in range(2)}
    summary = {"labels": labels, "counts": counts, "trainable": True}
    (root / "dataset-summary.json").write_text(json.dumps(summary), encoding="utf-8")

    for split in ("train", "validation", "test"):
        rows = []
        for class_id in range(2):
            # Prefix the ID with its split so normal fixtures remain disjoint.
            drawing_id = f"{split}-{class_id}"
            if duplicate_id and split == "validation" and class_id == 0:
                # Reuse a training ID to simulate a split-leakage defect.
                drawing_id = "train-0"
            rows.append(
                {
                    "split": split,
                    "class_id": class_id,
                    "drawing_id": drawing_id,
                    "group_id": drawing_id,
                    "trajectory_hash": f"hash-{split}-{class_id}",
                    "record_file": f"records/{split}/c{class_id:03d}.jsonl",
                    "byte_offset": 0,
                    "byte_length": 10,
                }
            )
        pq.write_table(pa.Table.from_pylist(rows), manifest_dir / f"{split}.parquet")
    return prepared


def test_audit_reports_balanced_labels_and_split_counts(tmp_path: Path) -> None:
    """Summarize each class and verify disjoint IDs across prepared splits."""
    prepared = _write_fixture(tmp_path)

    # Override production scale with fixture-sized expectations for this test.
    report = audit_prepared_dataset(
        prepared,
        expected_class_count=2,
        expected_per_class={"train": 1, "validation": 1, "test": 1},
    )

    # Confirm both the overall shape and leakage safeguards were reported.
    assert report["status"] == "passed"
    assert report["class_count"] == 2
    assert report["rows_by_split"] == {"train": 2, "validation": 2, "test": 2}
    assert report["ids_disjoint"] is True
    assert report["trajectories_disjoint"] is True


def test_audit_rejects_drawing_id_reused_across_splits(tmp_path: Path) -> None:
    """Never allow a drawing identity to leak between data partitions."""
    prepared = _write_fixture(tmp_path, duplicate_id=True)

    # A repeated identity must fail before the report can claim disjoint splits.
    with pytest.raises(ValueError, match="drawing ID appears in multiple rows"):
        audit_prepared_dataset(prepared, expected_class_count=2)
