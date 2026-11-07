"""Bounded, transactional SQLite storage for deterministic validation views."""

from __future__ import annotations

import json
import sqlite3
import zlib
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any

import numpy as np


class RenderCache:
    """Store lossless single-channel float32 views within a payload byte budget.

    Connections are short-lived and never cross worker boundaries. SQLite rolls
    back interrupted writes; database/permission/corruption errors remain visible.
    """

    def __init__(self, root: Path, max_bytes: int) -> None:
        """Create the shared cache database; reject nonpositive budgets."""
        if max_bytes <= 0:
            raise ValueError("cache_max_bytes must be positive")
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / "validation.sqlite3"
        self.max_bytes = max_bytes
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS views ("
                "sequence INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, "
                "metadata TEXT NOT NULL, image BLOB NOT NULL, size INTEGER NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS usage (id INTEGER PRIMARY KEY, bytes INTEGER)"
            )
            connection.execute("INSERT OR IGNORE INTO usage VALUES (1, 0)")
            used = connection.execute("SELECT bytes FROM usage WHERE id=1").fetchone()[
                0
            ]
            used = self._evict(connection, used, 0)
            connection.execute("UPDATE usage SET bytes=? WHERE id=1", (used,))

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Open a bounded page cache with a timeout for other worker writers."""
        with closing(sqlite3.connect(self.path, timeout=60)) as connection:
            connection.execute("PRAGMA cache_size=-2048")
            with connection:
                yield connection

    def _evict(self, connection: sqlite3.Connection, used: int, incoming: int) -> int:
        """Remove oldest rows until the new payload fits; return remaining usage."""
        while used + incoming > self.max_bytes:
            sequence, old_size = connection.execute(
                "SELECT sequence, size FROM views ORDER BY sequence LIMIT 1"
            ).fetchone()
            connection.execute("DELETE FROM views WHERE sequence=?", (sequence,))
            used -= old_size
        return used

    def get(self, key: str) -> dict[str, Any] | None:
        """Return a detached sample, or None on a cache miss."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT metadata, image FROM views WHERE key=?", (key,)
            ).fetchone()
        if row is None:
            return None
        sample = json.loads(row[0])
        # Only one identical channel is stored; expand without renormalizing.
        shape = sample.pop("_cache_shape")
        sample["image"] = (
            np.repeat(
                np.frombuffer(zlib.decompress(row[1]), dtype=np.float32).reshape(shape)[
                    None
                ],
                3,
                axis=0,
            )
            if shape is not None
            else None
        )
        return sample

    def put(self, key: str, sample: dict[str, Any]) -> None:
        """Publish a sample if space remains, retaining reusable rows when full."""
        metadata = dict(sample)
        image = metadata.pop("image", None)
        if image is not None:
            if (
                image.dtype != np.float32
                or image.ndim != 3
                or image.shape[0] != 3
                or not np.array_equal(image[0], image[1])
                or not np.array_equal(image[0], image[2])
            ):
                raise ValueError("Cache requires identical float32 image channels")
            metadata["_cache_shape"] = list(image.shape[1:])
            payload = zlib.compress(image[0].tobytes())
        else:
            metadata["_cache_shape"] = None
            payload = b""
        encoded = json.dumps(metadata, allow_nan=False)
        size = len(payload) + len(encoded.encode()) + len(key.encode())
        if size > self.max_bytes:
            return
        # A single writer transaction makes accounting and publication indivisible.
        # Keep the admitted subset when full: FIFO/LRU would miss on every sample
        # of repeated sequential validation passes larger than the cache budget.
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT 1 FROM views WHERE key=?", (key,)).fetchone():
                return
            used = connection.execute("SELECT bytes FROM usage WHERE id=1").fetchone()[
                0
            ]
            if used + size > self.max_bytes:
                return
            connection.execute(
                "INSERT INTO views(key, metadata, image, size) VALUES (?, ?, ?, ?)",
                (key, encoded, payload, size),
            )
            connection.execute("UPDATE usage SET bytes=? WHERE id=1", (used + size,))
