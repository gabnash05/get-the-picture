import base64
import hashlib
import zipfile
from unittest.mock import patch

from guesser_data.common import atomic_json, json_bytes, load_step, object_hash
from guesser_data.settings import Settings

_download = load_step("01-download")
trajectory_hash = _download.trajectory_hash
sample_full_stream = _download.sample_full_stream
save_candidates = _download.save_candidates
prepare = load_step("02-prepare").prepare
export_module = load_step("04-export")
export_dataset = export_module.export_dataset


def test_prepare_and_export_small_dataset(tmp_path):
    settings = Settings(tmp_path, profile="smoke")
    meta = {"class_id": 0, "source_name": "cat", "generation": "fixture"}
    atomic_json(settings.base / "labels.json", [meta | {}])
    lines = [
        json_bytes(
            {
                "key_id": str(i),
                "word": "cat",
                "recognized": True,
                "drawing": [[[i, i + 1], [0, i + 1], [0, 1]]],
            }
        )
        + b"\n"
        for i in range(30)
    ]
    lines.append(b"{malformed\n")
    payload = b"".join(lines)
    meta.update(
        size=str(len(payload)),
        md5Hash=base64.b64encode(hashlib.md5(payload).digest()).decode(),
    )
    rows, stats = sample_full_stream(lines, meta, settings)
    assert stats["counts"]["rejected:invalid_record"] == 1
    rows[0]["id_conflict"] = True
    rows[1]["record"]["drawing"] = rows[2]["record"]["drawing"]
    rows[1]["trajectory_hash"] = trajectory_hash(rows[1]["record"])
    rows[1]["content_sha256"] = object_hash(rows[1]["record"])
    save_candidates(settings, meta, rows, stats, source_kind="synthetic_validation")
    summary = prepare(settings)
    assert summary["counts"]["0"] == {"train": 16, "validation": 2, "test": 2}
    quarantine = (settings.base / "quarantine.jsonl").read_text(encoding="utf-8")
    assert rows[0]["drawing_id"] in quarantine
    assert "conflicting_id" in quarantine
    assert not (settings.base / "frozen.json").exists()
    assert not (settings.base / "qa" / "review-decisions.json").exists()
    with patch.object(export_module, "audit", wraps=export_module.audit) as audit_call:
        archives = export_dataset(settings)
        assert audit_call.call_count == 1
    import pyarrow.parquet as pq

    ids = []
    for split in ("train", "validation", "test"):
        ids.extend(
            pq.read_table(
                settings.base / "prepared/manifests" / f"{split}.parquet",
                columns=["drawing_id"],
            )
            .column("drawing_id")
            .to_pylist()
        )
    assert rows[0]["drawing_id"] not in ids
    assert len({rows[1]["drawing_id"], rows[2]["drawing_id"]} & set(ids)) <= 1
    with zipfile.ZipFile(archives["trainer"]["path"]) as archive:
        assert not any(
            "records/test/" in name or "manifests/test." in name
            for name in archive.namelist()
        )
    with zipfile.ZipFile(archives["held-out-test"]["path"]) as archive:
        assert "prepared/manifests/test.parquet" in archive.namelist()
