"""Compare Guesser Run A vs Run B from Lightning CSV logs and selection JSON."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


DEFAULT_CHECKPOINT_ROOT = Path(__file__).resolve().parents[1] / "checkpoints"
RUN_DIRS = {
    "A": "A_complete_only",
    "B": "B_partial",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare small-dataset Guesser A/B validation curves and best scores."
    )
    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        default=DEFAULT_CHECKPOINT_ROOT,
        help="Root containing A_complete_only/ and B_partial/.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Where to write comparison artifacts (default: <checkpoint-root>/ab_comparison).",
    )
    return parser.parse_args()


def _latest_metrics_csv(run_dir: Path) -> Path:
    candidates = sorted(run_dir.glob("logs/**/metrics.csv"))
    if not candidates:
        raise FileNotFoundError(
            f"No metrics.csv under {run_dir / 'logs'}. Finish training first."
        )
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _read_rows(metrics_csv: Path) -> list[dict[str, str]]:
    with metrics_csv.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for raw in reader:
            rows.append({(key or "").strip(): (value or "").strip() for key, value in raw.items()})
        return rows


def _float_or_none(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _row_get(row: dict[str, str], *names: str) -> str | None:
    lowered = {key.lower(): value for key, value in row.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value not in (None, ""):
            return value
    return None


def _epoch_series(rows: list[dict[str, str]], field: str) -> list[tuple[int, float]]:
    """Keep the last logged value per epoch for epoch-level metrics."""
    by_epoch: dict[int, float] = {}
    for row in rows:
        epoch_raw = _row_get(row, "epoch")
        value = _float_or_none(_row_get(row, field))
        if epoch_raw is None or value is None:
            continue
        by_epoch[int(float(epoch_raw))] = value
    return sorted(by_epoch.items())


def _best_val(rows: list[dict[str, str]]) -> dict[str, float | int | None]:
    best_acc = None
    best_epoch = None
    best_loss = None
    for epoch, acc in _epoch_series(rows, "val_acc"):
        if best_acc is None or acc > best_acc:
            best_acc = acc
            best_epoch = epoch
    loss_by_epoch = dict(_epoch_series(rows, "val_loss"))
    if best_epoch is not None:
        best_loss = loss_by_epoch.get(best_epoch)
    return {
        "best_val_acc": best_acc,
        "best_val_acc_epoch": best_epoch,
        "best_val_loss_at_best_acc": best_loss,
    }


def _load_selection(run_dir: Path) -> dict | None:
    path = run_dir / "checkpoint-selection.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _svg_polyline(
    series: list[tuple[int, float]],
    *,
    width: int = 720,
    height: int = 280,
    padding: int = 48,
    title: str,
    y_label: str,
    color: str,
) -> str:
    if not series:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><text x="24" y="40">No data for {title}</text></svg>\n'

    xs = [point[0] for point in series]
    ys = [point[1] for point in series]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if math.isclose(x_min, x_max):
        x_max = x_min + 1
    if math.isclose(y_min, y_max):
        y_max = y_min + 1e-6

    def map_x(epoch: int) -> float:
        return padding + (epoch - x_min) / (x_max - x_min) * (width - 2 * padding)

    def map_y(value: float) -> float:
        return height - padding - (value - y_min) / (y_max - y_min) * (height - 2 * padding)

    points = " ".join(f"{map_x(epoch):.1f},{map_y(value):.1f}" for epoch, value in series)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="{padding}" y="28" font-family="Segoe UI, sans-serif" font-size="16">{title}</text>
  <text x="16" y="{height / 2}" font-family="Segoe UI, sans-serif" font-size="12" transform="rotate(-90 16,{height / 2})">{y_label}</text>
  <line x1="{padding}" y1="{height - padding}" x2="{width - padding}" y2="{height - padding}" stroke="#333"/>
  <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height - padding}" stroke="#333"/>
  <polyline fill="none" stroke="{color}" stroke-width="2.5" points="{points}"/>
  <text x="{padding}" y="{height - 16}" font-family="Segoe UI, sans-serif" font-size="12">epoch {x_min} .. {x_max}</text>
  <text x="{width - padding - 120}" y="{height - 16}" font-family="Segoe UI, sans-serif" font-size="12">y {y_min:.4g} .. {y_max:.4g}</text>
</svg>
"""


def _dual_svg(
    series_a: list[tuple[int, float]],
    series_b: list[tuple[int, float]],
    *,
    title: str,
    y_label: str,
) -> str:
    width, height, padding = 800, 320, 52
    combined = series_a + series_b
    if not combined:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><text x="24" y="40">No data for {title}</text></svg>\n'

    xs = [point[0] for point in combined]
    ys = [point[1] for point in combined]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if math.isclose(x_min, x_max):
        x_max = x_min + 1
    if math.isclose(y_min, y_max):
        y_max = y_min + 1e-6

    def map_x(epoch: int) -> float:
        return padding + (epoch - x_min) / (x_max - x_min) * (width - 2 * padding)

    def map_y(value: float) -> float:
        return height - padding - (value - y_min) / (y_max - y_min) * (height - 2 * padding)

    def poly(series: list[tuple[int, float]]) -> str:
        return " ".join(
            f"{map_x(epoch):.1f},{map_y(value):.1f}" for epoch, value in series
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="{padding}" y="28" font-family="Segoe UI, sans-serif" font-size="16">{title}</text>
  <text x="18" y="{height / 2}" font-family="Segoe UI, sans-serif" font-size="12" transform="rotate(-90 18,{height / 2})">{y_label}</text>
  <line x1="{padding}" y1="{height - padding}" x2="{width - padding}" y2="{height - padding}" stroke="#333"/>
  <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height - padding}" stroke="#333"/>
  <polyline fill="none" stroke="#1f77b4" stroke-width="2.5" points="{poly(series_a)}"/>
  <polyline fill="none" stroke="#ff7f0e" stroke-width="2.5" points="{poly(series_b)}"/>
  <text x="{width - 180}" y="28" font-family="Segoe UI, sans-serif" font-size="12" fill="#1f77b4">A complete-only</text>
  <text x="{width - 180}" y="46" font-family="Segoe UI, sans-serif" font-size="12" fill="#ff7f0e">B partial</text>
  <text x="{padding}" y="{height - 16}" font-family="Segoe UI, sans-serif" font-size="12">epoch {x_min} .. {x_max}</text>
</svg>
"""


def _markdown_report(summary: dict) -> str:
    a = summary["A"]
    b = summary["B"]
    winner = summary["winner_by_best_val_acc"]
    lines = [
        "# Guesser small-dataset A/B comparison",
        "",
        f"- Prepared from checkpoint root: `{summary['checkpoint_root']}`",
        f"- Winner by best validation accuracy: **{winner}**",
        "",
        "| Run | Best val_acc | Epoch | Val loss @ best | Metrics CSV |",
        "| --- | ---: | ---: | ---: | --- |",
        (
            f"| A complete-only | {a['best_val_acc']} | {a['best_val_acc_epoch']} | "
            f"{a['best_val_loss_at_best_acc']} | `{a['metrics_csv']}` |"
        ),
        (
            f"| B partial | {b['best_val_acc']} | {b['best_val_acc_epoch']} | "
            f"{b['best_val_loss_at_best_acc']} | `{b['metrics_csv']}` |"
        ),
        "",
        "Plots: `val_acc.svg`, `val_loss.svg` (and per-run SVGs).",
        "",
        "Note: this compares Lightning validation on **complete** validation views during training. "
        "Full ten-stage / held-out evaluation remains the Validation owner's protocol.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    root = args.checkpoint_root
    output_dir = args.output_dir or (root / "ab_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)

    run_payload: dict[str, dict] = {}
    for label, folder in RUN_DIRS.items():
        run_dir = root / folder
        metrics_csv = _latest_metrics_csv(run_dir)
        rows = _read_rows(metrics_csv)
        stats = _best_val(rows)
        selection = _load_selection(run_dir)
        val_acc = _epoch_series(rows, "val_acc")
        val_loss = _epoch_series(rows, "val_loss")
        train_loss = _epoch_series(rows, "train_loss")
        run_payload[label] = {
            **stats,
            "metrics_csv": str(metrics_csv),
            "selection": selection,
            "val_acc_curve": val_acc,
            "val_loss_curve": val_loss,
            "train_loss_curve": train_loss,
        }
        (output_dir / f"{label}_val_acc.svg").write_text(
            _svg_polyline(val_acc, title=f"{label} val_acc", y_label="val_acc", color="#1f77b4"),
            encoding="utf-8",
        )
        (output_dir / f"{label}_val_loss.svg").write_text(
            _svg_polyline(val_loss, title=f"{label} val_loss", y_label="val_loss", color="#d62728"),
            encoding="utf-8",
        )

    a_best = run_payload["A"]["best_val_acc"]
    b_best = run_payload["B"]["best_val_acc"]
    if a_best is None and b_best is None:
        winner = "none"
    elif a_best is None:
        winner = "B"
    elif b_best is None:
        winner = "A"
    elif b_best > a_best:
        winner = "B"
    elif a_best > b_best:
        winner = "A"
    else:
        winner = "tie"

    summary = {
        "checkpoint_root": str(root.resolve()),
        "winner_by_best_val_acc": winner,
        "A": {
            "best_val_acc": run_payload["A"]["best_val_acc"],
            "best_val_acc_epoch": run_payload["A"]["best_val_acc_epoch"],
            "best_val_loss_at_best_acc": run_payload["A"]["best_val_loss_at_best_acc"],
            "metrics_csv": run_payload["A"]["metrics_csv"],
            "selection": run_payload["A"]["selection"],
        },
        "B": {
            "best_val_acc": run_payload["B"]["best_val_acc"],
            "best_val_acc_epoch": run_payload["B"]["best_val_acc_epoch"],
            "best_val_loss_at_best_acc": run_payload["B"]["best_val_loss_at_best_acc"],
            "metrics_csv": run_payload["B"]["metrics_csv"],
            "selection": run_payload["B"]["selection"],
        },
    }

    (output_dir / "val_acc.svg").write_text(
        _dual_svg(
            run_payload["A"]["val_acc_curve"],
            run_payload["B"]["val_acc_curve"],
            title="Validation accuracy: A vs B",
            y_label="val_acc",
        ),
        encoding="utf-8",
    )
    (output_dir / "val_loss.svg").write_text(
        _dual_svg(
            run_payload["A"]["val_loss_curve"],
            run_payload["B"]["val_loss_curve"],
            title="Validation loss: A vs B",
            y_label="val_loss",
        ),
        encoding="utf-8",
    )

    summary_path = output_dir / "comparison-summary.json"
    report_path = output_dir / "comparison.md"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(_markdown_report(summary), encoding="utf-8")

    print(f"Wrote {summary_path}")
    print(f"Wrote {report_path}")
    print(f"Wrote plots under {output_dir}")
    print(
        f"Best val_acc — A: {a_best} | B: {b_best} | winner: {winner}"
    )


if __name__ == "__main__":
    main()
