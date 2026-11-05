"""Editable defaults for the Guesser data workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = PACKAGE_ROOT / ".local/data"
EXAMPLE_DATA_ROOT = DEFAULT_DATA_ROOT / "example"
PROBE_DATA_ROOT = DEFAULT_DATA_ROOT / "probe"
SEED = 198173
CONCURRENCY = 2
DEFAULT_PREPROCESSOR = "foreground"
PROFILES = {
    "production": {"candidates": 5500, "train": 4000, "validation": 500, "test": 500},
    "smoke": {"candidates": 30, "train": 16, "validation": 2, "test": 2},
}
PREPROCESS_DEFAULTS = {
    "working_size": 512,
    "border": 16,
    "quantization": 16,
    "uniformity": 0.70,
    "distance": 24 / 255,
    "canny_low": 50,
    "canny_high": 150,
    "frame": 1,
    "dense_limit": 0.95,
    "fit": 192,
    "output": 224,
    "mean": 0.5,
    "std": 0.5,
    "render_canvas": 512,
    "render_fit": 448,
    "render_supersample": 2,
    "evaluation_width": 6,
    "training_width_min": 3,
    "training_width_max": 12,
}
COMPLETE_PROBABILITY = 0.2
PARTIAL_MIN = 0.1
PARTIAL_MAX = 0.9
BLANK_RETRIES = 8
EVALUATION_FRACTIONS = tuple(i / 10 for i in range(1, 11))


@dataclass(frozen=True)
class Settings:
    data_root: Path = DEFAULT_DATA_ROOT
    profile: str = "production"
    seed: int = SEED

    def __post_init__(self):
        object.__setattr__(self, "data_root", Path(self.data_root).resolve())
        if self.profile not in PROFILES:
            raise ValueError(f"Unknown data profile: {self.profile}")

    @property
    def base(self) -> Path:
        return self.data_root / self.profile

    @property
    def spec(self) -> dict[str, int]:
        values = dict(PROFILES[self.profile])
        values["final"] = sum(
            values[split] for split in ("train", "validation", "test")
        )
        return values
