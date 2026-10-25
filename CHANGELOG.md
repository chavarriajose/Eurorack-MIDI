# Changelog

## v0 (25 Oct 2026)

First working version, built and tested on a hand-soldered perfboard.

- 5 gate/trigger inputs sent to the computer as USB MIDI notes (channel 0)
- Clock input on Input_5, sent as MIDI Clock, Start and Stop (4 pulses per beat by default)
- 5 trigger/gate outputs driven by MIDI notes from the computer (channel 1)
- Input protection with a CD40106 Schmitt trigger buffer
- 5V outputs using 2N3904 transistor stages
- Schematics, bill of materials and documentation
