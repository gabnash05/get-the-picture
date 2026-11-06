"""PyTorch adapters over IndexedDrawings for complete-only and partial training."""

from __future__ import annotations

import hashlib
import random
from typing import Any

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

_images = load_step("06-images")
cut_prefix = _images.cut_prefix
preprocess = _images.preprocess
render_qd = _images.render_qd


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
    ) -> None:
        if split not in ("train", "validation"):
            raise ValueError(f"Unsupported training split: {split}")
        self.prepared_dir = prepared_dir
        self.split = split
        self.complete_only = complete_only
        self.epoch = epoch
        self.candidate = candidate
        self.drawings = IndexedDrawings(self.prepared_dir, self.split)
        self._length = len(self.drawings)
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
        self.epoch = int(epoch)

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
        if self.split == "train" and not self.complete_only:
            return self.drawings.training_image(
                index, epoch=self.epoch, candidate=self.candidate
            )

        item = self.drawings[index]
        result = _complete_view(item["record"], self.epoch, candidate=self.candidate)
        return {
            **result,
            "class_id": item["class_id"],
            "drawing_id": item["drawing_id"],
        }

    def __getstate__(self) -> dict[str, Any]:
        state = dict(self.__dict__)
        # IndexedDrawings already clears handles across process forks.
        return state


class GuesserDataModule(L.LightningDataModule):
    """Train/validation loaders for Run A (complete-only) or Run B (partial)."""

    def __init__(
        self,
        prepared_dir: str,
        batch_size: int = 32,
        num_workers: int = 0,
        complete_only: bool = False,
        candidate: str = DEFAULT_PREPROCESSOR,
    ) -> None:
        super().__init__()
        self.prepared_dir = prepared_dir
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.complete_only = complete_only
        self.candidate = candidate
        self.train_dataset: GuesserDataset | None = None
        self.val_dataset: GuesserDataset | None = None

    def setup(self, stage: str | None = None) -> None:
        if stage in (None, "fit"):
            self.train_dataset = GuesserDataset(
                self.prepared_dir,
                split="train",
                complete_only=self.complete_only,
                candidate=self.candidate,
                augment=True,
            )
            self.val_dataset = GuesserDataset(
                self.prepared_dir,
                split="validation",
                complete_only=True,
                candidate=self.candidate,
                augment=False,
            )

    def train_dataloader(self) -> DataLoader:
        if self.train_dataset is None:
            self.setup("fit")
        assert self.train_dataset is not None
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=torch.cuda.is_available(),
        )

    def val_dataloader(self) -> DataLoader:
        if self.val_dataset is None:
            self.setup("fit")
        assert self.val_dataset is not None
        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=torch.cuda.is_available(),
        )
