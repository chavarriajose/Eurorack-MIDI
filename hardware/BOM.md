# Bill of materials (v0)

Everything needed for the full build: 5 inputs and 5 outputs.

## Main parts

| Qty | Part | Value / type | Used for | Notes |
|---|---|---|---|---|
| 1 | ESP32-S3 development board | ESP32-S3-DevKitC-1 style, N16R8 | Microcontroller, USB MIDI | On clone boards, bridge the IN-OUT pad (see README) |
| 1 | CD40106 | Hex Schmitt inverter, DIP-14 | Input buffer, U1 | |
| 1 | IC socket | DIP-14 | Socket for the CD40106 | Recommended |
| 5 | NPN transistor | 2N3904 | Output stages | BC547 or BC548 also work (check the pinout, it is reversed) |
| 10 | 3.5 mm mono jack | e.g. Thonkiconn PJ398SM | 5 inputs + 5 outputs | |

## Resistors

| Qty | Value | Used for |
|---|---|---|
| 5 | 22k | Input series resistor |
| 10 | 100k | Input pull-down (5), output base pull-down (5) |
| 5 | 10k | Output base resistor |
| 10 | 1k | Output pull-up to 5V (5), output series resistor (5) |

## Diodes and capacitors

| Qty | Part | Used for | Notes |
|---|---|---|---|
| 10 | 1N5819 Schottky diode | Input clamps, 2 per input | 1N4148 works as a substitute |
| 1 | 0.22µF film capacitor | Decoupling for the CD40106 | A 100nF ceramic capacitor also works |

## Build materials

| Qty | Part | Notes |
|---|---|---|
| 1 | Perfboard, 54 x 33 holes (2.54 mm pitch) | About half of it is used |
| 2 | Female pin header, 1 x 22 | Socket for the ESP32 board, so it can be removed |
| | Hook-up wire, solid core | For jumpers and the jack wiring |
| 1 | USB-C cable | To the computer |
