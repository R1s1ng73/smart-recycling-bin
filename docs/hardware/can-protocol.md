# CAN bus: water-bin transmitter interface

Source: [WaterBin_ALL_Final.ino](../../firmware/arduino/WaterBin_ALL_Final/WaterBin_ALL_Final.ino). This specifies the *intended messages in the archived transmitting sketch*; it is not a capture of actual bus traffic.

## Configuration

| Item | Value |
| --- | --- |
| Controller | MCP2515 over SPI |
| Chip select | Arduino pin 10 |
| CAN bitrate configuration | 500 kbit/s |
| Controller clock configuration | 8 MHz |
| Controller mode | Normal mode |
| Message identifiers | Standard 11-bit IDs |
| Payload length | One byte |

## Transmitted status values

| CAN arbitration ID | Data byte | Enum in code | Meaning assigned in code |
| --- | --- | --- | --- |
| 0x0F6 | 0x01 | CLEAN_BUCKET_FULL | Clean-water sensor active |
| 0x0F6 | 0x02 | CLEAN_BUCKET_EMPTY | Clean-water sensor inactive |
| 0x036 | 0x03 | SEWAGE_BUCKET_FULL | Sewage-water sensor active |
| 0x036 | 0x04 | SEWAGE_BUCKET_EMPTY | Sewage-water sensor inactive |

An input is treated as active when its digital read is LOW. The code sends on *sensor state change*. Physical interpretation of FULL versus EMPTY depends on sensor location and has not been verified. A separate variable named myCanID (0x001) is declared but not used by these send branches.

## What is confirmed and what is missing

- Present in Arduino source: MCP2515 initialization, CAN IDs, one-byte payloads, and calls to sendMessage.
- Missing **from recovered original source**: Raspberry Pi-side CAN receiver, bus wiring/termination verification, successful capture logs, and end-to-end hardware tests. A separate [new reconstructed Pi CAN reader](pi-can-receiver.md) exists, but it has not been validated with physical hardware.
- Main-bin RFID uses serial output ('UID:' + identifier) and the Pi Python app includes an optional serial RFID parser. That is **UART**, not evidence of Pi CAN reception.
- The firmware logs a sent message after the call but does not check the return status; it cannot establish acknowledgment or delivery.

## Suggested independent verification (future work)

1. Confirm the actual Arduino model, MCP2515 oscillator and transceiver voltage requirements.
2. Verify supply, grounds, CAN H/CAN L and physical termination safely before applying power.
3. Compile the archived Arduino code for the real board and resolve board-specific interrupt and I/O issues.
4. Use appropriate CAN receiving hardware to record real frame IDs, data, bus errors and communication rate.
5. A [replacement Pi receiver demonstration](pi-can-receiver.md) is provided. It is explicitly labeled *reconstructed*, not recovered original code.

No automotive ECU integration, automotive safety validation, production-grade reliability or completed Pi CAN receive path is claimed.
