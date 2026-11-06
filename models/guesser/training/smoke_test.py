"""Limited-batch GPU smoke for the Guesser training adapters."""

from __future__ import annotations

from pathlib import Path

import lightning as L

try:
    from .dataset import GuesserDataModule
    from .module import GuesserViTModule
except ImportError:
    from dataset import GuesserDataModule
    from module import GuesserViTModule

PREPARED_DIR = (
    Path(__file__).resolve().parents[1] / "data" / ".local" / "data" / "small" / "prepared"
)


def run_smoke_test(complete_only: bool = False) -> None:
    mode = "A complete-only" if complete_only else "B partial"
    print(f"Initializing DataModule ({mode})...")
    dm = GuesserDataModule(
        prepared_dir=str(PREPARED_DIR),
        batch_size=4,
        num_workers=0,
        complete_only=complete_only,
    )
    dm.setup("fit")

    print("Initializing ViT-Tiny LightningModule...")
    model = GuesserViTModule(num_classes=345)

    print("Setting up limited-batch Lightning Trainer...")
    trainer = L.Trainer(
        max_epochs=1,
        accelerator="gpu",
        devices=1,
        limit_train_batches=1,
        limit_val_batches=1,
        enable_checkpointing=False,
        logger=False,
    )

    print("Running sanity check fit loop (1 train batch, 1 val batch)...")
    trainer.fit(model, datamodule=dm)
    print(f"Smoke test passed for {mode}.")


if __name__ == "__main__":
    run_smoke_test(complete_only=False)
    run_smoke_test(complete_only=True)
