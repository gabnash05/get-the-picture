"""Independently audit prepared Guesser labels and Parquet manifests."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import pyarrow.parquet as pq

PRODUCTION_SPLIT_COUNTS = {"train": 4000, "validation": 500, "test": 500}
SPLITS = tuple(PRODUCTION_SPLIT_COUNTS)


def _read_json(path: Path) -> Any:
    """Load a UTF-8 JSON document with a path-specific error on failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read valid JSON from {path}") from exc


def _validate_labels(labels: Any, expected_class_count: int) -> dict[int, str]:
    """Require the ordered class registry to contain each integer ID once."""
    if not isinstance(labels, list) or len(labels) != expected_class_count:
        raise ValueError(
            f"Expected {expected_class_count} labels; found "
            f"{len(labels) if isinstance(labels, list) else 'invalid data'}"
        )

    names: dict[int, str] = {}
    for expected_id, label in enumerate(labels):
        # Class IDs are model outputs, so their position must match the registry order.
        if (
            not isinstance(label, dict)
            or type(label.get("class_id")) is not int
            or label["class_id"] != expected_id
            or not isinstance(label.get("source_name"), str)
            or not label["source_name"].strip()
        ):
            raise ValueError(f"Invalid label registry entry at position {expected_id}")
        names[expected_id] = label["source_name"]
    # Distinct names prevent a valid-looking registry from aliasing two output classes.
    if len(set(names.values())) != expected_class_count:
        raise ValueError("Label source names must be unique")
    return names


def _validate_manifest_row(
    row: dict[str, Any], split: str, label_names: dict[int, str]
) -> tuple[str, str]:
    """Check a manifest row's split, identity, class, and indexed-path metadata."""
    class_id = row.get("class_id")
    drawing_id = row.get("drawing_id")
    group_id = row.get("group_id")
    trajectory_hash = row.get("trajectory_hash")
    record_file = row.get("record_file")
    byte_offset = row.get("byte_offset")
    byte_length = row.get("byte_length")

    if row.get("split") != split:
        raise ValueError(f"Manifest row has the wrong split in {split}")
    if type(class_id) is not int or class_id not in label_names:
        raise ValueError(f"Manifest row has an unknown class ID in {split}")
    if not isinstance(drawing_id, str) or not drawing_id or group_id != drawing_id:
        raise ValueError(f"Invalid drawing/group identity in {split}")
    if not isinstance(trajectory_hash, str) or not trajectory_hash:
        raise ValueError(f"Missing trajectory hash in {split}")
    # Require paths to stay inside the manifest's own split before using offsets later.
    if (
        not isinstance(record_file, str)
        or PurePosixPath(record_file).is_absolute()
        or ".." in PurePosixPath(record_file).parts
        or not record_file.startswith(f"records/{split}/")
    ):
        raise ValueError(f"Invalid record path in {split}")
    if (
        type(byte_offset) is not int
        or byte_offset < 0
        or type(byte_length) is not int
        or byte_length < 1
    ):
        raise ValueError(f"Invalid byte range in {split}")
    return drawing_id, trajectory_hash


def audit_prepared_dataset(
    prepared_path: str | Path,
    *,
    expected_class_count: int = 345,
    expected_per_class: dict[str, int] | None = None,
    batch_size: int = 4096,
) -> dict[str, Any]:
    """Audit ordered labels, split manifests, counts, and cross-split uniqueness.

    This is a manifest audit: it does not read indexed JSONL payloads or inspect
    rendered images. The data package's `audit` command performs that deeper check.
    SQLite keeps ID/hash uniqueness checks disk-backed for large production sets.
    """
    if expected_class_count < 1 or batch_size < 1:
        raise ValueError("expected_class_count and batch_size must be positive")
    if expected_per_class is not None and set(expected_per_class) != set(SPLITS):
        raise ValueError(f"expected_per_class must define exactly {SPLITS}")

    # Locate labels and manifests relative to `prepared/`, not the caller's cwd.
    prepared = Path(prepared_path).expanduser().resolve()
    base = prepared.parent
    labels = _read_json(base / "labels.json")
    label_names = _validate_labels(labels, expected_class_count)
    summary = _read_json(base / "dataset-summary.json")
    if summary.get("labels") != labels:
        raise ValueError("Dataset summary labels do not match labels.json")
    if expected_class_count == 345 and summary.get("trainable") is not True:
        raise ValueError("Expected a trainable production dataset")

    summary_counts = summary.get("counts")
    if not isinstance(summary_counts, dict):
        raise TypeError("Dataset summary split counts must be an object")
    # Pre-seed every class and split so missing classes remain visible as zeroes.
    counts_by_class = {class_id: {split: 0 for split in SPLITS} for class_id in label_names}
    rows_by_split = {split: 0 for split in SPLITS}
    database_columns = [
        "split",
        "class_id",
        "drawing_id",
        "group_id",
        "trajectory_hash",
        "record_file",
        "byte_offset",
        "byte_length",
    ]

    with tempfile.TemporaryDirectory(prefix="guesser-manifest-audit-") as temporary_dir:
        connection = sqlite3.connect(Path(temporary_dir) / "identities.sqlite")
        try:
            # Global unique indexes catch drawing or trajectory leakage across all splits.
            connection.execute(
                "CREATE TABLE seen (drawing_id TEXT PRIMARY KEY, "
                "trajectory_hash TEXT UNIQUE, split TEXT NOT NULL)"
            )
            for split in SPLITS:
                manifest_path = prepared / "manifests" / f"{split}.parquet"
                if not manifest_path.is_file():
                    raise FileNotFoundError(f"Missing split manifest: {manifest_path}")
                parquet_file = pq.ParquetFile(manifest_path)
                missing_columns = set(database_columns) - set(parquet_file.schema.names)
                if missing_columns:
                    raise ValueError(
                        f"{manifest_path} is missing columns: {sorted(missing_columns)}"
                    )
                # Bounded Parquet batches keep a full 345-class scan out of RAM.
                for batch in parquet_file.iter_batches(
                    batch_size=batch_size, columns=database_columns
                ):
                    for row in batch.to_pylist():
                        drawing_id, digest = _validate_manifest_row(row, split, label_names)
                        try:
                            # Insert into one shared table so duplicates across split files fail.
                            connection.execute(
                                "INSERT INTO seen VALUES (?, ?, ?)",
                                (drawing_id, digest, split),
                            )
                        except sqlite3.IntegrityError as exc:
                            # Name the violated identity explicitly instead of hiding the cause.
                            if connection.execute(
                                "SELECT 1 FROM seen WHERE drawing_id = ?", (drawing_id,)
                            ).fetchone():
                                raise ValueError(
                                    f"drawing ID appears in multiple rows: {drawing_id}"
                                ) from exc
                            raise ValueError(
                                f"trajectory hash appears in multiple rows: {digest}"
                            ) from exc
                        counts_by_class[row["class_id"]][split] += 1
                        rows_by_split[split] += 1
                    # Bound SQLite's pending transaction work to the current manifest batch.
                    connection.commit()
        finally:
            connection.close()

    # Reconcile observed rows against the exporter summary and the planned split contract.
    summary_by_class = {int(class_id): values for class_id, values in summary_counts.items()}
    if set(summary_by_class) != set(label_names):
        raise ValueError("Dataset summary class IDs do not match labels.json")
    for class_id, counts in counts_by_class.items():
        if summary_by_class[class_id] != counts:
            raise ValueError(f"Dataset summary count mismatch for class {class_id}")
        if expected_per_class is not None and counts != expected_per_class:
            raise ValueError(f"Unexpected split count for class {class_id}: {counts}")

    # Mark the limits in the result so consumers don't mistake this for a payload audit.
    return {
        "status": "passed",
        "prepared_path": str(prepared),
        "class_count": len(label_names),
        "rows_by_split": rows_by_split,
        "counts_by_class": [
            {"class_id": class_id, "source_name": label_names[class_id], **counts}
            for class_id, counts in counts_by_class.items()
        ],
        "ids_disjoint": True,
        "trajectories_disjoint": True,
        "manifest_only": True,
        "payload_and_image_audit_required": True,
    }
