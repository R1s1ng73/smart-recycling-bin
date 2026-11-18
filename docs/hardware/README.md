# ModuCycle — archived hardware architecture

This document explains the hardware shown in the original EE3070 team design drawings and the two surviving Arduino sketches. It complements the Pi-side Python computer-vision prototype, but it does not establish that every planned module was completed or end-to-end tested.

## Modules in the original design

| Module | Components shown in drawings | Firmware evidence |
| --- | --- | --- |
| Main bin | Raspberry Pi 5, Arduino, camera, RFID, CAN module, relay compressor, fill-level and fire sensors | Archived Main_Bin_Final.ino has RFID, ultrasonic, gas/fire sensor and compressor control logic |
| Water bin | Arduino, pump relay, clean and sewage water sensors | Archived WaterBin_ALL_Final.ino has sensor, pump and CAN-transmit logic |
| Slave bin | Arduino, MCP2515, fire/fill sensors, compressor | Described in diagrams; no dedicated slave-bin sketch archived |

The original circuit drawing includes 12 V input and DC-DC conversion to 5 V. This is a *design schematic*, not a validated power budget or certified wiring diagram.

## Conceptual signal-flow diagram

~~~mermaid
flowchart LR
    CAM[Camera] --> PI[Raspberry Pi Python vision]
    RFID[MFRC522 RFID] --> MAIN[Main-bin Arduino]
    ULTRA[Ultrasonic and other sensors] --> MAIN
    MAIN -->|Serial UID messages| PI
    MAIN --> RELAY[Compressor relay]
    WATERLEVEL[Water-level sensors] --> WATER[Water-bin Arduino]
    WATER --> PUMP[Pump relay]
    WATER -->|SPI| MCP[MCP2515]
    MCP -->|CAN status frames| BUS[CAN bus design]
    BUS -.->|receiver implementation unavailable| RX[Other controller / Pi CAN receiver unverified]
~~~

**Boundary:** The current Python repo supports optional UART/serial RFID reading, not a Pi CAN receiver. The water-bin Arduino sketch contains MCP2515 CAN transmission calls. These are distinct interfaces and have not been verified together in this source archive.

## Source files and further reading

- [Main-bin Arduino sketch](../../firmware/arduino/Main_Bin_Final/Main_Bin_Final.ino)
- [Water-bin Arduino sketch](../../firmware/arduino/WaterBin_ALL_Final/WaterBin_ALL_Final.ino)
- [CAN message format](can-protocol.md)
- [Firmware review notes](firmware-notes.md)

The original team PDFs are not copied into this public repo: the project materials include other students' identifying details, and permission to publish all original diagrams has not been established. This is a privacy-conscious written summary instead.

## Attribution and verification

ModuCycle was a four-member university team project. The original proposal assigned the member associated with this repository cloud-server, image-recognition, NB-IoT and card-reading work; these were **proposed responsibilities**, not individually verified outcomes. Arduino sketches are preserved as team artifacts, not presented as sole-authored or production-ready code. The exact board models, as-built wiring, and end-to-end test results remain unverified.
