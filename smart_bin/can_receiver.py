"""Reconstructed, read-only SocketCAN receiver for the ModuCycle water-bin protocol.

This is NEW example code based on archived Arduino transmit frames, not
the lost original Raspberry Pi CAN implementation. No physical CAN link has
been verified. The module does not control pumps, motors, or actuators.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import sys
from types import SimpleNamespace
from typing import Any, Sequence

SEWAGE_ID = 0x036
CLEAN_WATER_ID = 0x0F6

# Mapping copied from the archived WaterBin_ALL_Final.ino CAN-transmit branches.
# "FULL" / "EMPTY" are firmware labels, not validated water-level measurements.
_STATUS_MAP = {
    (CLEAN_WATER_ID, 0x01): ("clean_water", "CLEAN_BUCKET_FULL", True),
    (CLEAN_WATER_ID, 0x02): ("clean_water", "CLEAN_BUCKET_EMPTY", False),
    (SEWAGE_ID, 0x03): ("sewage_water", "SEWAGE_BUCKET_FULL", True),
    (SEWAGE_ID, 0x04): ("sewage_water", "SEWAGE_BUCKET_EMPTY", False),
}


@dataclass(frozen=True)
class BucketStatus:
    arbitration_id: int
    bucket: str
    firmware_status: str
    sensor_active: bool
    payload_hex: str


def decode_bucket_status(frame: Any) -> BucketStatus | None:
    """Decode one valid, one-byte *standard CAN* water-status frame.

    Return None for unrelated identifiers, malformed frames, error/remote
    frames, extended-ID frames and CAN-FD frames. Accept duck-typed messages
    so protocol decoding is testable without python-can or physical hardware.
    """
    if any((
        getattr(frame, "is_extended_id", False),
        getattr(frame, "is_remote_frame", False),
        getattr(frame, "is_error_frame", False),
        getattr(frame, "is_fd", False),
    )):
        return None

    can_id = getattr(frame, "arbitration_id", None)
    if can_id not in (SEWAGE_ID, CLEAN_WATER_ID):
        return None
    try:
        payload = bytes(frame.data)
    except (AttributeError, TypeError, ValueError):
        return None
    if len(payload) != 1:
        return None
    dlc = getattr(frame, "dlc", None)
    if dlc is not None and dlc != 1:
        return None
    definition = _STATUS_MAP.get((can_id, payload[0]))
    if definition is None:
        return None
    bucket, status, sensor_active = definition
    return BucketStatus(
        arbitration_id=can_id,
        bucket=bucket,
        firmware_status=status,
        sensor_active=sensor_active,
        payload_hex=f"{payload[0]:02X}",
    )


def format_status(status: BucketStatus, *, as_json: bool = False) -> str:
    """Format a decoded frame with a receive-time timestamp (not sensor time)."""
    received_at = datetime.now(timezone.utc).isoformat()
    if as_json:
        return json.dumps({"received_at_utc": received_at, **asdict(status)},
                          ensure_ascii=False)
    state = "ACTIVE" if status.sensor_active else "INACTIVE"
    return (f"{received_at}  id=0x{status.arbitration_id:03X}  "
            f"bucket={status.bucket}  sensor={state}  "
            f"firmware={status.firmware_status}  data={status.payload_hex}")


def _synthetic_frames() -> list[Any]:
    """Example CAN frames for a demo; NEVER claim these came from hardware."""
    return [
        SimpleNamespace(arbitration_id=can_id, data=bytes([value]),
                        dlc=1, is_extended_id=False, is_remote_frame=False,
                        is_error_frame=False, is_fd=False)
        for can_id, value in (
            (CLEAN_WATER_ID, 0x01), (CLEAN_WATER_ID, 0x02),
            (SEWAGE_ID, 0x03), (SEWAGE_ID, 0x04),
        )
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only ModuCycle Pi-side CAN status receiver (reconstructed demo).")
    parser.add_argument("--channel", default="can0",
                        help="Linux SocketCAN interface (can0, vcan0; default: can0)")
    parser.add_argument("--demo", action="store_true",
                        help="Print synthetic sample frames; no CAN hardware or python-can needed")
    parser.add_argument("--json", action="store_true",
                        help="Output one JSON object per received/decoded frame")
    parser.add_argument("--count", type=int,
                        help="Exit after this many valid frames (default: run until Ctrl+C)")
    args = parser.parse_args(argv)
    if args.count is not None and args.count < 1:
        parser.error("--count must be a positive integer")

    if args.demo:
        print("SYNTHETIC DEMO ONLY: these are not physical CAN captures.", file=sys.stderr)
        frames = _synthetic_frames()
        if args.count is not None:
            frames = frames[:args.count]
        for frame in frames:
            decoded = decode_bucket_status(frame)
            if decoded is not None:
                print(format_status(decoded, as_json=args.json), flush=True)
        return 0

    try:
        import can  # optional dependency, required only for real SocketCAN
    except ImportError:
        print("python-can is missing: pip install -r requirements-can.txt",
              file=sys.stderr)
        return 2

    filters = [
        {"can_id": SEWAGE_ID, "can_mask": 0x7FF, "extended": False},
        {"can_id": CLEAN_WATER_ID, "can_mask": 0x7FF, "extended": False},
    ]
    received = 0
    try:
        with can.Bus(interface="socketcan", channel=args.channel,
                     can_filters=filters, receive_own_messages=False) as bus:
            print(f"Listening on {args.channel} (read-only). Ctrl+C to stop.",
                  file=sys.stderr)
            while args.count is None or received < args.count:
                frame = bus.recv(timeout=1.0)
                if frame is None:
                    continue
                decoded = decode_bucket_status(frame)
                if decoded is None:
                    continue
                print(format_status(decoded, as_json=args.json), flush=True)
                received += 1
    except KeyboardInterrupt:
        print("\nStopped by user.", file=sys.stderr)
        return 0
    except (OSError, can.CanError) as exc:
        print(f"Could not receive CAN frames on {args.channel}: {exc}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
