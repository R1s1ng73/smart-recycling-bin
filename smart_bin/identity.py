"""QR code decoding and optional Arduino/UART RFID input."""

from smart_bin.logic import normalise_user_id


def scan_qr_code(frame_bgr: object) -> str | None:
    """Decode a user ID using OpenCV; no system-level zbar package needed."""
    import cv2

    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(frame_bgr)
    return normalise_user_id(data) if data else None


def parse_rfid_line(raw_line: str) -> str | None:
    """Expected serial protocol: 'UID: <identifier>\\n'."""
    line = raw_line.strip()
    if not line.startswith("UID:"):
        return None
    return normalise_user_id(line[4:])


class RFIDReader:
    """Read RFID UIDs from an Arduino or another UART device, if configured."""

    def __init__(self, port: str, baudrate: int = 9600) -> None:
        import serial

        self.serial = serial.Serial(port, baudrate=baudrate, timeout=0)

    def read_uid(self) -> str | None:
        if not self.serial.is_open or not self.serial.in_waiting:
            return None
        data = self.serial.readline().decode("utf-8", errors="replace")
        return parse_rfid_line(data)

    def close(self) -> None:
        if self.serial.is_open:
            self.serial.close()
