# Archived Arduino firmware: review notes

The original sketches have been added *without silently changing their logic*. Review warnings below are source-code observations, not an assertion that the system passed a hardware test.

## Main-bin Arduino

Source: [Main_Bin_Final.ino](../../firmware/arduino/Main_Bin_Final/Main_Bin_Final.ino)

- MFRC522 RFID with a serial message beginning 'UID:'.
- Ultrasonic fill-level measurement and relay-controlled compressor logic, using a 10 cm threshold and a five-second stability window.
- Analog smoke, gas and fire detection, SHT31 temperature/humidity and pressure-input reads.
- A maximum compressor-cycle counter of three is configured.

**Code review concerns**

- The expression `((44 - distance) / 44) * 100` performs integer division before conversion to float; it likely produces incorrect continuous fill-level percentages.
- The pressure sensor is configured as A6 but a debug message says 'A3 Value'.
- RFID UID bytes are concatenated as decimal values without separators; decoding can be ambiguous.
- Blocking loops and actuator behavior need safety and bench testing before use.

## Water-bin Arduino

Source: [WaterBin_ALL_Final.ino](../../firmware/arduino/WaterBin_ALL_Final/WaterBin_ALL_Final.ino)

- Reads two digital water sensors, a button and controls a relay for a pump.
- Sends one-byte status-change CAN frames through an MCP2515 configured at 500 kbit/s with 8 MHz oscillator setting.
- CAN protocol details: [can-protocol.md](can-protocol.md).

**Code review concerns**

- The button interrupt uses `digitalPinToInterrupt(6)`; pin 6 is not an external-interrupt pin on some common Arduino boards. Confirm the actual board.
- A variable changed by the interrupt handler is not declared volatile; check interrupt safety and debounce.
- Initial digitalRead calls happen at global initialization before setup configures the relevant input pins.
- Return codes from CAN sendMessage are not checked, so 'Message sent' text is not proof of successful delivery.
- Blocking delays and loops may postpone monitoring and shutdown reactions.

## Scope and team attribution

The current Pi Python app is a cleaned-up portfolio prototype for vision, user identity and record logging. It does not control an autonomous physical sorter. The original EE3070 team proposal outlines planned NB-IoT, cloud and physical modules, not independently verified deployments. Exact Arduino board models, the physical build, electrical safety and end-to-end Pi/Arduino CAN communication remain unverified. A [new Pi receiver demonstration](pi-can-receiver.md) is included separately, but the missing historical receiver has not been recovered. Present this as work by a university project team and specify personal contributions only where confirmed.
