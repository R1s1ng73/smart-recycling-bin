# Reconstructed Raspberry Pi CAN status receiver

> **Provenance:** This is a **new, reconstructed, read-only demonstration**, written from the original Arduino `WaterBin_ALL_Final.ino` transmit protocol. It is **not** the missing original Raspberry Pi source code, and no Raspberry Pi ↔ Arduino end-to-end test has been performed.

## What it does

- Connects to an existing Linux **SocketCAN** interface (`can0` for real hardware or `vcan0` for simulation).
- Receives standard 11-bit CAN frames only, filtering for arbitration IDs `0x036` (sewage) and `0x0F6` (clean water).
- Decodes the four **one-byte status codes** from the archived water-bin firmware (see [CAN protocol](can-protocol.md)).
- Prints timestamps, CAN ID, bucket, boolean `sensor_active` and the original firmware status name; use `--json` for JSON-lines output.
- **Never sends CAN frames, toggles GPIO, starts motors or commands pumps.** Unknown/invalid messages are ignored.

The firmware calls these states `FULL` and `EMPTY`, but sensor wiring/mounting has not been verified. The receiver reports the original firmware label alongside an **active/inactive** sensor interpretation rather than making a physical fill-level claim. The Arduino **only sends on status changes**, so the receiver may print nothing until a sensor changes state.

## A. No-hardware demo (any OS)

From the repository root:

~~~bash
python -m smart_bin.can_receiver --demo
python -m smart_bin.can_receiver --demo --json
python -m pytest -q tests/test_can_receiver.py
~~~

The demo prints a prominent **SYNTHETIC DEMO** warning. The four printed frames are generated in Python, not measurements from a real bus. The protocol decoder can run without `python-can` in this mode.

## B. Virtual CAN bus test (Linux, including Raspberry Pi OS)

Install the optional receiver dependency and Linux tools:

~~~bash
python -m pip install -r requirements-can.txt
sudo apt install can-utils iproute2
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set vcan0 up
~~~

First terminal — start receiving and stop after two valid frames:

~~~bash
python -m smart_bin.can_receiver --channel vcan0 --json --count 2
~~~

Second terminal — inject sample frames:

~~~bash
cansend vcan0 036#03
cansend vcan0 0F6#01
~~~

Expected decoded statuses: `SEWAGE_BUCKET_FULL` and `CLEAN_BUCKET_FULL`. These are **synthetic test frames**, not data from an Arduino. With two terminals the receiver must be running *before* sending the frames. If you already have `vcan0`, skip `ip link add`.

## C. Real Raspberry Pi + MCP2515 hardware (not verified)

**Prerequisites:** Raspberry Pi running a Linux OS with SocketCAN; a suitable **3.3 V-compatible** CAN controller/transceiver interface (e.g. properly level-matched MCP2515 board or compatible USB-CAN adapter); a CAN transceiver at the Arduino end; and appropriate CAN H, CAN L and common reference grounding. The classic Pi GPIO/SPI interface is **not 5 V tolerant**. Do not connect an unverified 5 V SPI module directly to Pi GPIO.

If you use an MCP2515 on Pi SPI, its Linux device-tree overlay may look like this in the Raspberry Pi boot configuration (`/boot/firmware/config.txt` on recent Raspberry Pi OS):

~~~ini
dtparam=spi=on
# EXAMPLE ONLY. Replace oscillator and interrupt with the Pi module's actual
# crystal frequency (in Hz) and BCM GPIO connected to MCP2515 INT.
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
~~~

**Do not copy this configuration blindly.** Your old Arduino firmware configures **its own** MCP2515 at 8 MHz, but the Raspberry Pi MCP2515 board could have a *different* oscillator. The Pi overlay value must match the clock on the **Pi-side module**; `interrupt=25` assumes an INT wire at BCM GPIO25. Confirm the chip-select/SPI bus, transceiver voltage, interrupt GPIO and configuration against your particular board first. Reboot after a correct overlay configuration and check the CAN interface:

~~~bash
ip -details link show can0
sudo ip link set can0 up type can bitrate 500000
ip -details -statistics link show can0
python -m smart_bin.can_receiver --channel can0
~~~

Use **500,000 bit/s** because the archived Arduino water-bin sketch sets `CAN_500KBPS`. CAN H/L must be connected through appropriate CAN transceivers, with **120 Ω termination at each physical end of the bus** (not at every node). Verify power and wiring with hardware off before connecting devices. A one-node/standalone CAN network may not get proper acknowledgment; have a compatible second CAN node or a suitable tester. Never connect this prototype wiring to a vehicle or EV high-voltage system without qualified supervision and the relevant safety controls.

## Problems to check

| Symptom | Likely checks |
| --- | --- |
| `can0` absent | SPI disabled, incorrect device-tree overlay, wrong Pi MCP2515 oscillator, INT or chip-select wiring, kernel driver |
| Interface present but no frames | Incorrect bitrate, transceiver power, CAN H/L, termination, no changes of water state, Arduino source not running |
| CAN bus-off / errors | Bad physical wiring, missing second active node/ACK, bitrate mismatch, short or incompatible transceiver |
| Decoder prints no output on injected frame | Only IDs `0x036`/`0x0F6`, standard CAN frame, exactly one expected data byte |
| `ModuleNotFoundError: can` | Run `python -m pip install -r requirements-can.txt` |

See the upstream [python-can SocketCAN documentation](https://python-can.readthedocs.io/en/stable/interfaces/socketcan.html) for the supported API and `vcan` setup.

## Verification and disclosure

- The **decoder** has hardware-free unit tests.
- The **end-to-end physical bus**, exact Pi CAN module, original lost receiver, MCU firmware compile status and electrical safety **have not been validated here**.
- The receiver is a **new educational/portfolio reconstruction**. It is not the deployed original and does not add CAN support to the existing Streamlit application automatically.
