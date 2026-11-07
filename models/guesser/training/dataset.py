"""PyTorch adapters over IndexedDrawings for complete-only and partial training."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import random
from pathlib import Path
from typing import Any, cast

import lightning as L
import torch
from guesser_data import IndexedDrawings
from guesser_data.common import load_step
from guesser_data.settings import (
    BLANK_RETRIES,
    DEFAULT_PREPROCESSOR,
    PREPROCESS_DEFAULTS,
    SEED,
)
from torch.utils.data import DataLoader, Dataset
from torchvision.transforms import v2

if __package__:
    from .render_cache import RenderCache
else:
    from render_cache import RenderCache

_images = load_step("06-images")
cut_prefix = _images.cut_prefix
preprocess = _images.preprocess
render_qd = _images.render_qd


def _file_freshness(path: Path) -> tuple[int, ...]:
    """Identify source replacement/edits without invalidating on ordinary reads."""
    stat = path.stat()
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def _seeded_rng(*parts: object) -> random.Random:
    key = "|".join(str(part) for part in parts).encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def _complete_view(
    record: dict[str, Any],
    epoch: int,
    candidate: str = DEFAULT_PREPROCESSOR,
) -> dict[str, Any]:
    """Render a full original with bounded blank retries (Run A / validation)."""
    width_rng = _seeded_rng(SEED, record["key_id"], epoch, "width")
    width = width_rng.uniform(
        PREPROCESS_DEFAULTS["training_width_min"],
        PREPROCESS_DEFAULTS["training_width_max"],
    )
    result: dict[str, Any] | None = None
    for attempt in range(BLANK_RETRIES):
        result = preprocess(render_qd(cut_prefix(record, 1.0), width), candidate)
        if result["status"] != "blank":
            return {
                **result,
                "fraction": 1.0,
                "width": width,
                "attempt": attempt,
                "skipped": result["status"] == "uncertain",
            }
    assert result is not None
    return {
        **result,
        "fraction": 1.0,
        "width": width,
        "attempt": BLANK_RETRIES - 1,
        "skipped": True,
    }


class GuesserDataset(Dataset):
    """One split of prepared originals as model tensors.

    Train + ``complete_only=False`` uses ``training_image`` (20% full / 10%-90%).
    Train + ``complete_only=True`` and all validation samples use full originals.
    """

    def __init__(
        self,
        prepared_dir: str,
        split: str = "train",
        complete_only: bool = False,
        epoch: int = 0,
        candidate: str = DEFAULT_PREPROCESSOR,
        augment: bool = False,
        cache_dir: str | Path | None = None,
        cache_max_bytes: int = 2 * 1024**3,
        manifest_cache_dir: str | Path | None = None,
    ) -> None:
        if split not in ("train", "validation"):
            raise ValueError(f"Unsupported training split: {split}")
        self.prepared_dir = prepared_dir
        self.split = split
        self.complete_only = complete_only
        # Shared Torch storage survives fork and spawn without context-specific
        # multiprocessing semaphores. Publish only between loader iterations.
        self._epoch = torch.tensor(int(epoch), dtype=torch.int64).share_memory_()
        self.candidate = candidate
        self.drawings = IndexedDrawings(
            self.prepared_dir, self.split, manifest_cache_dir=manifest_cache_dir
        )
        self._length = len(self.drawings)
        self.cache = (
            RenderCache(Path(cache_dir), cache_max_bytes)
            if cache_dir is not None and split == "validation"
            else None
        )
        if self.cache is not None:
            # Hash this split's manifest and recipe, not held-out records.
            # Each lookup separately checks the indexed record file's freshness.
            manifest = Path(prepared_dir) / "manifests" / f"{split}.parquet"
            self._cache_manifest = manifest.resolve()
            self._cache_manifest_stat = _file_freshness(self._cache_manifest)
            recipe = {
                "schema": "validation-complete-v1",
                "prepared": str(Path(prepared_dir).resolve()),
                "manifest": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                "candidate": candidate,
                "config": _images.candidate_hash(candidate),
                "seed": SEED,
                "retries": BLANK_RETRIES,
                "implementation": [
                    hashlib.sha256(Path(path).read_bytes()).hexdigest()
                    for path in (__file__, _images.__file__)
                ],
                "libraries": {
                    name: importlib.metadata.version(name)
                    for name in ("numpy", "pillow", "opencv-python-headless")
                },
            }
            self._cache_identity = hashlib.sha256(
                json.dumps(recipe, sort_keys=True).encode()
            ).hexdigest()
        self.augment = (
            v2.Compose(
                [
                    v2.RandomAffine(
                        degrees=10,
                        translate=(0.05, 0.05),
                        scale=(0.9, 1.1),
                    ),
                ]
            )
            if augment
            else None
        )

    def __len__(self) -> int:
        return self._length

    def set_epoch(self, epoch: int) -> None:
        """Publish a training epoch to existing persistent workers."""
        self.epoch = int(epoch)

    @property
    def epoch(self) -> int:
        """Read the shared epoch in the parent or a worker process."""
        return int(self._epoch.item())

    @epoch.setter
    def epoch(self, epoch: int) -> None:
        """Update the shared epoch between loader iterations."""
        self._epoch.fill_(int(epoch))

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        for offset in range(self._length):
            index = (idx + offset) % self._length
            sample = self._read_sample(index)
            if (
                sample.get("skipped")
                or sample.get("image") is None
                or sample.get("status") != "ok"
            ):
                continue

            image = torch.from_numpy(sample["image"])
            if self.augment is not None:
                image = self.augment(image)
            return {
                "image": image,
                "class_id": torch.tensor(sample["class_id"], dtype=torch.long),
            }

        raise RuntimeError(f"No usable image near index {idx} in split {self.split}")

    def _read_sample(self, index: int) -> dict[str, Any]:
        """Fetch a view, caching only reusable validation renders."""
        key = None
        if self.cache is not None:
            if _file_freshness(self._cache_manifest) != self._cache_manifest_stat:
                raise RuntimeError("Validation manifest changed; recreate the dataset")
            row = self.drawings.manifest_row(index)
            source = (Path(self.prepared_dir) / row["record_file"]).resolve()
            if not source.is_relative_to(Path(self.prepared_dir).resolve()):
                raise ValueError("Invalid indexed cache source path")
            identity = (
                self._cache_identity,
                index,
                self.epoch,
                str(source),
                _file_freshness(source),
            )
            key = hashlib.sha256(repr(identity).encode()).hexdigest()
            cached = self.cache.get(key)
            if cached is not None:
                return cached
        if self.split == "train" and not self.complete_only:
            return self.drawings.training_image(
                index, epoch=self.epoch, candidate=self.candidate
            )

        item = self.drawings[index]
        result = _complete_view(item["record"], self.epoch, candidate=self.candidate)
        sample = {
            **result,
            "class_id": item["class_id"],
            "drawing_id": item["drawing_id"],
        }
        if self.cache is not None and key is not None:
            self.cache.put(key, sample)
        return sample

    def __getstate__(self) -> dict[str, Any]:
        state = dict(self.__dict__)
        # IndexedDrawings already clears handles across process forks.
        return state


class EpochDataLoader(DataLoader):
    """Publish Lightning's current epoch before creating/prefetching an iterator."""

    def __init__(self, *args: Any, epoch_source: Any = None, **kwargs: Any) -> None:
        """Keep the epoch source in the parent; workers receive only the dataset."""
        super().__init__(*args, **kwargs)
        self.epoch_source = epoch_source

    def __iter__(self):
        """Set shared epoch state before PyTorch dispatches any worker requests."""
        trainer = getattr(self.epoch_source, "trainer", None)
        if trainer is not None:
            cast(GuesserDataset, self.dataset).set_epoch(trainer.current_epoch)
        return super().__iter__()


class GuesserDataModule(L.LightningDataModule):
    """Train/validation loaders for Run A (complete-only) or Run B (partial)."""

    def __init__(
        self,
        prepared_dir: str,
        batch_size: int = 32,
        num_workers: int = 0,
        complete_only: bool = False,
        candidate: str = DEFAULT_PREPROCESSOR,
        cache_dir: str | Path | None = None,
        cache_max_bytes: int = 2 * 1024**3,
        manifest_cache_dir: str | Path | None = None,
    ) -> None:
        super().__init__()
        self.prepared_dir = prepared_dir
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.complete_only = complete_only
        self.candidate = candidate
        self.train_dataset: GuesserDataset | None = None
        self.cache_dir = cache_dir
        self.cache_max_bytes = cache_max_bytes
        self.manifest_cache_dir = manifest_cache_dir
        self.val_dataset: GuesserDataset | None = None

    def setup(self, stage: str | None = None) -> None:
        if stage in (None, "fit"):
            self.train_dataset = GuesserDataset(
                self.prepared_dir,
                split="train",
                complete_only=self.complete_only,
                candidate=self.candidate,
                augment=True,
                manifest_cache_dir=self.manifest_cache_dir,
            )
            self.val_dataset = GuesserDataset(
                self.prepared_dir,
                split="validation",
                complete_only=True,
                candidate=self.candidate,
                augment=False,
                cache_dir=self.cache_dir,
                cache_max_bytes=self.cache_max_bytes,
                manifest_cache_dir=self.manifest_cache_dir,
            )
            if self.manifest_cache_dir is not None:
                # Build native manifest files serially before starting workers.
                # Each worker subsequently maps those buffers, not a decoded copy.
                for dataset in (self.train_dataset, self.val_dataset):
                    if len(dataset):
                        dataset.drawings.manifest_row(0)

    def _dataloader(self, dataset: GuesserDataset, *, shuffle: bool) -> DataLoader:
        options: dict = {
            "batch_size": self.batch_size,
            "shuffle": shuffle,
            "num_workers": self.num_workers,
            "pin_memory": torch.cuda.is_available(),
        }
        if self.num_workers > 0:
            # Prefetch/render on CPU workers while the GPU trains.
            options["persistent_workers"] = True
            options["prefetch_factor"] = 2
        if dataset.split == "train":
            return EpochDataLoader(dataset, epoch_source=self, **options)
        return DataLoader(dataset, **options)

    def train_dataloader(self) -> DataLoader:
        if self.train_dataset is None:
            self.setup("fit")
        assert self.train_dataset is not None
        return self._dataloader(self.train_dataset, shuffle=True)

    def val_dataloader(self) -> DataLoader:
        if self.val_dataset is None:
            self.setup("fit")
        assert self.val_dataset is not None
        return self._dataloader(self.val_dataset, shuffle=False)
