"""Hardware-free tests for reconstructed ModuCycle CAN status decoder."""

import json
from types import SimpleNamespace

import pytest

from smart_bin.can_receiver import (
    CLEAN_WATER_ID, SEWAGE_ID, decode_bucket_status, main,
)


def make_frame(can_id, value, **kwargs):
    fields = dict(arbitration_id=can_id, data=bytes([value]), dlc=1,
                  is_extended_id=False, is_remote_frame=False,
                  is_error_frame=False, is_fd=False)
    fields.update(kwargs)
    return SimpleNamespace(**fields)


@pytest.mark.parametrize("can_id,payload,bucket,enum,active", [
    (CLEAN_WATER_ID, 0x01, "clean_water", "CLEAN_BUCKET_FULL", True),
    (CLEAN_WATER_ID, 0x02, "clean_water", "CLEAN_BUCKET_EMPTY", False),
    (SEWAGE_ID, 0x03, "sewage_water", "SEWAGE_BUCKET_FULL", True),
    (SEWAGE_ID, 0x04, "sewage_water", "SEWAGE_BUCKET_EMPTY", False),
])
def test_all_archived_statuses(can_id, payload, bucket, enum, active):
    result = decode_bucket_status(make_frame(can_id, payload))
    assert result is not None
    assert (result.arbitration_id, result.bucket, result.firmware_status,
            result.sensor_active, result.payload_hex) == (
                can_id, bucket, enum, active, f"{payload:02X}")


@pytest.mark.parametrize("change", [
    {"arbitration_id": 0x123},
    {"data": b""},
    {"data": b"\x03\x04"},
    {"data": b"\x55"},
    {"dlc": 0},
    {"dlc": 2},
    {"is_extended_id": True},
    {"is_remote_frame": True},
    {"is_error_frame": True},
    {"is_fd": True},
])
def test_ignores_invalid_or_unrelated_frames(change):
    assert decode_bucket_status(make_frame(SEWAGE_ID, 0x03, **change)) is None


def test_rejects_matching_code_on_wrong_arbitration_id():
    assert decode_bucket_status(make_frame(CLEAN_WATER_ID, 0x03)) is None


def test_rejects_missing_payload():
    assert decode_bucket_status(SimpleNamespace(arbitration_id=SEWAGE_ID)) is None


def test_synthetic_demo_json_has_four_valid_messages(capsys):
    assert main(["--demo", "--json"]) == 0
    captured = capsys.readouterr()
    records = [json.loads(x) for x in captured.out.splitlines()]
    assert len(records) == 4
    assert [x["firmware_status"] for x in records] == [
        "CLEAN_BUCKET_FULL", "CLEAN_BUCKET_EMPTY",
        "SEWAGE_BUCKET_FULL", "SEWAGE_BUCKET_EMPTY",
    ]
    assert all("received_at_utc" in row for row in records)
    assert "SYNTHETIC DEMO" in captured.err


def test_demo_count_stops_after_one(capsys):
    assert main(["--demo", "--count", "1"]) == 0
    assert len(capsys.readouterr().out.splitlines()) == 1
