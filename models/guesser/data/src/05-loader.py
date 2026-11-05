"""Small, process-local indexed loader; no model or PyTorch dependency."""

from __future__ import annotations

import bisect
import hashlib
import json
import os
import random
from collections import OrderedDict
from collections.abc import Iterator
from pathlib import Path

from .common import DataError, load_step
from .settings import (
    BLANK_RETRIES,
    COMPLETE_PROBABILITY,
    DEFAULT_PREPROCESSOR,
    EVALUATION_FRACTIONS,
    PARTIAL_MAX,
    PARTIAL_MIN,
    PREPROCESS_DEFAULTS,
    SEED,
)

_images = load_step("06-images")
cut_prefix = _images.cut_prefix
preprocess = _images.preprocess
render_qd = _images.render_qd


class IndexedDrawings:
    """Seek records using Parquet offsets; handles and row caches belong to one PID.

    Supply the prepared/ folder of a prepared dataset. The model consumes only the
    resulting image and class_id; raw record metadata are for auditing.

    Flow: read one original -> cut by time -> render -> preprocess one image.
    PyTorch DataLoader batching belongs to the model project.
    """

    def __init__(
        self,
        prepared: str | Path,
        split: str = "train",
        max_handles: int = 8,
        cached_row_groups: int = 2,
    ):
        if (
            split not in ("train", "validation", "test")
            or max_handles < 1
            or cached_row_groups < 1
        ):
            raise DataError("Invalid loader configuration", "invalid_loader")
        self.prepared = Path(prepared).resolve()
        self.split = split
        self.max_handles = max_handles
        self.cached_row_groups = cached_row_groups
        import pyarrow.parquet as pq

        metadata = pq.ParquetFile(
            self.prepared / "manifests" / f"{split}.parquet"
        ).metadata
        self.ends = []
        total = 0
        for row_group_index in range(metadata.num_row_groups):
            total += metadata.row_group(row_group_index).num_rows
            self.ends.append(total)
        self.total = total
        self._reset()

    def _reset(self):
        self._pid = os.getpid()
        self._handles = OrderedDict()
        self._rows = OrderedDict()
        self._parquet = None

    def _check_process(self):
        if self._pid != os.getpid():
            self.close()
            self._pid = os.getpid()

    def __len__(self) -> int:
        return self.total

    def manifest_row(self, index: int) -> dict:
        self._check_process()
        if index < 0:
            index += self.total
        if not 0 <= index < self.total:
            raise IndexError(index)
        import pyarrow.parquet as pq

        group = bisect.bisect_right(self.ends, index)
        if group not in self._rows:
            if self._parquet is None:
                self._parquet = pq.ParquetFile(
                    self.prepared / "manifests" / f"{self.split}.parquet"
                )
            self._rows[group] = self._parquet.read_row_group(group).to_pylist()
            if len(self._rows) > self.cached_row_groups:
                self._rows.popitem(last=False)
        self._rows.move_to_end(group)
        return self._rows[group][index - (self.ends[group - 1] if group else 0)]

    def __getitem__(self, index: int) -> dict:
        row = self.manifest_row(index)
        path = (self.prepared / row["record_file"]).resolve()
        if not path.is_relative_to(self.prepared):
            raise DataError("Invalid indexed path", "invalid_path")
        if path not in self._handles:
            self._handles[path] = path.open("rb")
            if len(self._handles) > self.max_handles:
                self._handles.popitem(last=False)[1].close()
        self._handles.move_to_end(path)
        source = self._handles[path]
        source.seek(row["byte_offset"])
        raw = source.read(row["byte_length"])
        record = json.loads(raw)
        if len(raw) != row["byte_length"] or record["key_id"] != row["drawing_id"]:
            raise DataError("Indexed record changed; audit package", "audit_failed")
        return {
            "class_id": row["class_id"],
            "drawing_id": row["drawing_id"],
            "record": record,
        }

    def training_image(
        self, index: int, epoch: int, candidate: str = DEFAULT_PREPROCESSOR
    ) -> dict:
        """Read one training original and return its seeded, preprocessed time view."""
        if self.split != "train":
            raise DataError(
                "Training views require training originals", "invalid_split"
            )
        item = self[index]
        result = training_view(item["record"], epoch, candidate=candidate)
        return {
            **result,
            "class_id": item["class_id"],
            "drawing_id": item["drawing_id"],
        }

    def evaluation_images(
        self, index: int, candidate: str = DEFAULT_PREPROCESSOR
    ) -> Iterator[dict]:
        """Read one evaluation original and yield its ten fixed time views."""
        if self.split not in ("validation", "test"):
            raise DataError(
                "Evaluation views require validation/test originals", "invalid_split"
            )
        item = self[index]
        for result in evaluation_views(item["record"], candidate):
            yield {
                **result,
                "class_id": item["class_id"],
                "drawing_id": item["drawing_id"],
            }

    def close(self) -> None:
        for handle in getattr(self, "_handles", {}).values():
            handle.close()
        self._handles = OrderedDict()
        self._rows = OrderedDict()
        self._parquet = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def __getstate__(self):
        state = dict(self.__dict__)
        state.update(
            _handles=OrderedDict(), _rows=OrderedDict(), _parquet=None, _pid=-1
        )
        return state

    def __del__(self):
        self.close()


def _rng(seed, record, epoch, purpose, attempt=0):
    key = f"views-v1|{seed}|{record['key_id']}|{epoch}|{purpose}|{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def training_view(
    record: dict, epoch: int, seed: int = SEED, candidate: str = DEFAULT_PREPROCESSOR
) -> dict:
    """Choose a repeatable full/partial view from drawing ID, epoch and purpose."""
    width = _rng(seed, record, epoch, "width").uniform(
        PREPROCESS_DEFAULTS["training_width_min"],
        PREPROCESS_DEFAULTS["training_width_max"],
    )
    for attempt in range(BLANK_RETRIES):
        rng = _rng(seed, record, epoch, "cut", attempt)
        fraction = (
            1.0
            if rng.random() < COMPLETE_PROBABILITY
            else rng.uniform(PARTIAL_MIN, PARTIAL_MAX)
        )
        result = preprocess(render_qd(cut_prefix(record, fraction), width), candidate)
        if result["status"] != "blank":
            return {
                **result,
                "fraction": fraction,
                "width": width,
                "attempt": attempt,
                "skipped": result["status"] == "uncertain",
            }
    return {
        **result,
        "fraction": fraction,
        "width": width,
        "attempt": attempt,
        "skipped": True,
    }


def evaluation_views(record: dict, candidate: str = DEFAULT_PREPROCESSOR):
    """Yield all ten evaluation stages, including blank or unchanged views."""
    previous = None
    for fraction in EVALUATION_FRACTIONS:
        prefix = cut_prefix(record, fraction)
        rendered = render_qd(prefix)
        key = hashlib.sha256(rendered.tobytes()).hexdigest()
        result = preprocess(rendered, candidate)
        yield {**result, "fraction": fraction, "unchanged": key == previous}
        previous = key
