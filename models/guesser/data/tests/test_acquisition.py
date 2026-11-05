import base64
import hashlib
import json

import pytest

from guesser_data.common import DataError, candidate_path, load_step, receipt_path
from guesser_data.settings import Settings

source = load_step("01-download")
sample_full_stream = source.sample_full_stream
save_candidates = source.save_candidates
verify_receipt = source.verify_receipt


def _source(records):
    lines = [(json.dumps(record) + "\n").encode() for record in records]
    data = b"".join(lines)
    meta = {
        "class_id": 0,
        "source_name": "cat",
        "generation": "1",
        "size": str(len(data)),
        "md5Hash": base64.b64encode(hashlib.md5(data).digest()).decode(),
    }
    return lines, meta


def _record(drawing_id, end):
    return {
        "key_id": drawing_id,
        "word": "cat",
        "drawing": [[[0, end], [0, 1], [0, 1]]],
    }


def test_sample_order_and_retained_conflicts(tmp_path):
    settings = Settings(tmp_path, "smoke")
    records = [_record("a", 2), _record("b", 3), _record("a", 4)]
    lines, meta = _source(records)
    rows, _ = sample_full_stream(lines, meta, settings, keep=2)
    reverse, reverse_meta = _source(list(reversed(records)))
    other, _ = sample_full_stream(reverse, reverse_meta, settings, keep=2)
    assert rows == other
    assert next(row for row in rows if row["drawing_id"] == "a")["id_conflict"]


def test_receipt_checksum_and_resume(tmp_path):
    settings = Settings(tmp_path, "smoke")
    lines, meta = _source([_record("a", 2)])
    rows, stats = sample_full_stream(lines, meta, settings, keep=1)
    saved = save_candidates(settings, meta, rows, stats, keep=1)
    assert verify_receipt(settings, meta) == saved
    with pytest.raises(DataError):
        sample_full_stream(lines, {**meta, "md5Hash": "bad"}, settings, keep=1)
    with pytest.raises(DataError):
        verify_receipt(settings, {**meta, "generation": "changed"})
    before = receipt_path(settings, 0).read_bytes()

    def interrupted():
        yield lines[0]
        raise OSError("interrupted")

    with pytest.raises(OSError):
        sample_full_stream(interrupted(), meta, settings, keep=1)
    assert receipt_path(settings, 0).read_bytes() == before
    candidate_path(settings, 0).write_bytes(b"tampered")
    with pytest.raises(DataError):
        verify_receipt(settings, meta)
