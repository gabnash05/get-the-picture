from __future__ import annotations

import base64
import hashlib
import html
from importlib.resources import files

from PIL import Image, ImageDraw

from .common import DataError, atomic_json, json_bytes, load_step
from .settings import Settings

_loader = load_step("05-loader")
_images = load_step("06-images")
IndexedDrawings = _loader.IndexedDrawings
cut_prefix = _images.cut_prefix
render_qd = _images.render_qd


def generate_preview(settings: Settings) -> dict:
    """Create optional contact sheets from prepared training originals only."""
    output = settings.base / "preview"
    output.mkdir(parents=True, exist_ok=True)
    links = []
    with IndexedDrawings(settings.base / "prepared", "train") as drawings:
        grouped: dict[int, list[int]] = {}
        for index in range(len(drawings)):
            row = drawings.manifest_row(index)
            class_id = row["class_id"]
            if len(grouped.get(class_id, [])) < 8:
                grouped.setdefault(class_id, []).append(index)
        for class_id, indices in grouped.items():
            sheet = Image.new("RGB", (800, 440), "white")
            draw = ImageDraw.Draw(sheet)
            for index, record_index in enumerate(indices):
                item = drawings[record_index]
                image = render_qd(cut_prefix(item["record"], 1.0))
                image.thumbnail((190, 190))
                x, y = (index % 4) * 200, (index // 4) * 220
                sheet.paste(image, (x + 5, y))
                draw.text((x + 5, y + 193), str(item["drawing_id"]), fill="black")
            path = output / f"c{class_id:03d}.png"
            sheet.save(path)
            links.append(
                f'<li><a href="{html.escape(path.name)}">Class {class_id}</a></li>'
            )
    index_path = output / "index.html"
    index_path.write_text(
        '<!doctype html><meta charset="utf-8"><title>Training preview</title>'
        "<h1>Training drawings</h1><ul>" + "".join(links) + "</ul>",
        encoding="utf-8",
    )
    return {"classes": len(links), "index": str(index_path)}


def create_example(settings: Settings) -> dict:
    """Build a small, clearly synthetic one-class smoke example."""
    download = load_step("01-download")
    prepare = load_step("02-prepare").prepare

    if settings.profile != "smoke":
        raise DataError("Example requires the smoke profile", "invalid_profile")
    if (settings.base / "labels.json").exists() or (
        settings.base / "inventory.json"
    ).exists():
        raise DataError("Example destination already contains data", "example_exists")
    names = (
        files("guesser_data")
        .joinpath("resources/categories.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    registry = [{"class_id": i, "source_name": name} for i, name in enumerate(names)]
    label = registry[64]
    lines = []
    for index in range(settings.spec["candidates"]):
        x = index * 2
        record = {
            "key_id": f"synthetic-064-{index:06d}",
            "word": "cat",
            "recognized": True,
            "timestamp": "2000-01-01 00:00:00 UTC",
            "countrycode": "ZZ",
            "synthetic_validation": True,
            "drawing": [
                [[x, x + 10, x + 20], [0, 10, 5], [100, 300, 400]],
                [[x + 2, x + 18], [20, 22], [900, 1100]],
            ],
        }
        lines.append(json_bytes(record) + b"\n")
    payload = b"".join(lines)
    meta = {
        **label,
        "name": "synthetic/64.ndjson",
        "generation": "synthetic-v1",
        "size": str(len(payload)),
        "md5Hash": base64.b64encode(hashlib.md5(payload).digest()).decode("ascii"),
    }
    atomic_json(settings.base / "labels.json", registry)
    atomic_json(
        settings.base / "inventory.json",
        {"source_kind": "synthetic_validation", "categories": [meta]},
    )
    candidates, stats = download.sample_full_stream(lines, meta, settings)
    save_candidates(
        settings, meta, candidates, stats, source_kind="synthetic_validation"
    )
    summary = prepare(settings)
    preview = generate_preview(settings)
    example_dir = settings.base / "preview"
    with IndexedDrawings(settings.base / "prepared", "train") as drawings:
        record = drawings[0]["record"]
    for fraction in (0.1, 0.5, 1.0):
        render_qd(cut_prefix(record, fraction)).save(
            example_dir / f"time-{int(fraction * 100):03d}.png"
        )
    return {"summary": summary, "preview": preview, "synthetic": True}
