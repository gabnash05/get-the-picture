from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any, BinaryIO

from .settings import SEED, Settings


class DataError(Exception):
    def __init__(
        self, message: str, code: str = "data_error", hint: str = "", **details: Any
    ):
        super().__init__(message)
        self.code = code
        self.hint = hint
        self.details = details


def json_bytes(value: Any) -> bytes:
    """Canonical bytes for identity hashes and one-record-per-line storage."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def object_hash(value: Any) -> str:
    return sha256_bytes(json_bytes(value))


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path, default: Any = None) -> Any:
    path = Path(path)
    if not path.exists():
        if default is not None:
            return default
        raise DataError(f"Missing artifact: {path}", "missing_artifact")
    return json.loads(path.read_text(encoding="utf-8"))


@contextmanager
def atomic_output(path: Path) -> Iterator[BinaryIO]:
    """Publish a file only after its writer closes successfully."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".part", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as output:
            yield output
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def atomic_bytes(path: Path, data: bytes) -> None:
    with atomic_output(path) as output:
        output.write(data)


def atomic_json(path: Path, value: Any) -> None:
    # Human-readable metadata; json_bytes stays compact for hashes and JSONL.
    text = json.dumps(
        value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
    )
    atomic_bytes(Path(path), (text + "\n").encode("utf-8"))


def priority(namespace: str, drawing_id: str, seed: int = SEED) -> int:
    return int.from_bytes(
        hashlib.sha256(f"{namespace}|{seed}|{drawing_id}".encode("utf-8")).digest(),
        "big",
    )


def acquisition_recipe(settings: Settings, keep: int | None = None) -> dict[str, Any]:
    return {
        "version": "acquisition-v1",
        "seed": settings.seed,
        "cleaning": "clean-v1",
        "canonical": "trajectory-v1",
        "selection": "select-v1",
        "keep": keep or settings.spec["candidates"],
    }


def labels(settings: Settings) -> list[dict[str, Any]]:
    value = read_json(settings.base / "labels.json")
    return value["labels"] if isinstance(value, dict) else value


def candidate_path(settings: Settings, class_id: int) -> Path:
    return settings.base / "candidates" / f"c{class_id:03d}.jsonl"


def receipt_path(settings: Settings, class_id: int) -> Path:
    return settings.base / "receipts" / f"c{class_id:03d}.json"


def iter_jsonl(path: Path) -> Iterator[Any]:
    with Path(path).open("rb") as source:
        for line in source:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, values: Iterable[Any]) -> str:
    """Write seekable records atomically and return their file checksum."""
    digest = hashlib.sha256()
    with atomic_output(path) as output:
        for value in values:
            line = json_bytes(value) + b"\n"
            output.write(line)
            digest.update(line)
    return digest.hexdigest()


def load_step(name: str) -> ModuleType:
    """Import one numbered stage using Python's standard module loader."""
    return import_module("." + name, package=__package__)
