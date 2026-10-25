/*
  Eurorack-MIDI (v0)

  Two-way bridge between a eurorack modular synth and a computer,
  working as a USB MIDI device called "Eurorack-MIDI".

  - 5 input jacks send MIDI notes on channel 0 (gate high = Note On,
    gate low = Note Off). Input 5 can also be used as a clock input,
    sent to the computer as MIDI Clock, Start and Stop.
  - 5 output jacks are fired by MIDI notes received on channel 1.

  See README.md for the circuit, the settings and how to use it.

  Before uploading, set Tools > USB Mode to "USB-OTG (TinyUSB)".

  Created 25 Oct 2026
  by Jose Chavarria

  This code was partially written with the help of AI.

  Licensed under Creative Commons Attribution-ShareAlike 4.0
  (CC BY-SA 4.0). https://creativecommons.org/licenses/by-sa/4.0/
*/

#include "USB.h"
#include "USBMIDI.h"

#if ARDUINO_USB_MODE
#error "Set Tools > USB Mode to 'USB-OTG (TinyUSB)' to use USB MIDI."
#endif

const char* deviceName = "Eurorack-MIDI";

// MIDI channels (0-15, shown as 1-16 in most DAWs):
const byte inputChannel = 0;    // eurorack to computer
const byte outputChannel = 1;   // computer to eurorack

// input jacks (Input_1 to Input_5):
const int numInputs = 5;
const int inputPins[numInputs] = { 15, 16, 17, 18, 6 };
const byte inputNotes[numInputs] = { 36, 38, 39, 42, 46 };  // kick, snare, clap, closed hat, open hat
const byte inputVelocity = 100;
const bool inputInverted = true;          // the CD40106 inverts the signal
const unsigned long debounceTime = 2000;  // microseconds
const unsigned long minNoteLength = 10;   // ms

// clock input:
const bool useClockInput = true;
const int clockJack = 4;                  // 0 = Input_1 ... 4 = Input_5
const bool clockSendsNote = true;         // the clock jack also sends its note
const int clockPulsesPerBeat = 4;         // must divide 24 (1, 2, 3, 4, 6, 8, 12, 24)
const bool sendStartStop = true;
const unsigned long clockTimeout = 2000;  // ms without pulses = clock stopped
const bool printBpm = false;              // Serial Monitor on the UART port, 115200

// output jacks (Output_1 to Output_5):
const int numOutputs = 5;
const int outputPins[numOutputs] = { 8, 9, 10, 11, 12 };
const byte outputNotes[numOutputs] = { 36, 38, 39, 42, 46 };

enum JackMode { TRIGGER_MODE, GATE_MODE };
const JackMode outputModes[numOutputs] = {
  TRIGGER_MODE, TRIGGER_MODE, TRIGGER_MODE, TRIGGER_MODE, TRIGGER_MODE
};
const unsigned long triggerLength = 10;   // ms
const bool outputInverted = true;         // the transistor stage inverts the signal

// MIDI real-time messages:
const byte midiClock = 0xF8;
const byte midiStart = 0xFA;
const byte midiStop = 0xFC;

USBMIDI MIDI;

struct InputJack {
  bool gateIsHigh;
  unsigned long lastChange;     // microseconds
  bool noteIsOn;
  unsigned long noteOnTime;     // ms
  bool noteOffPending;
};
InputJack inputs[numInputs];

struct OutputJack {
  bool triggerRunning;
  unsigned long triggerEnd;     // ms
};
OutputJack outputs[numOutputs];

// clock state:
const int ticksPerPulse = 24 / clockPulsesPerBeat;  // MIDI clock = 24 ticks per beat
bool clockRunning = false;
bool haveInterval = false;
unsigned long lastPulseTime = 0;
unsigned long pulseInterval = 125000;   // starts at a 120 BPM guess
unsigned long tickInterval = 0;
unsigned long nextTickTime = 0;
int ticksLeft = 0;
unsigned long pulseCount = 0;
float bpm = 0;


void setup() {
  // outputs first, so the jacks go low as early as possible:
  for (int i = 0; i < numOutputs; i++) {
    pinMode(outputPins[i], OUTPUT);
    outputs[i].triggerRunning = false;
    setOutput(i, false);
  }

  for (int i = 0; i < numInputs; i++) {
    pinMode(inputPins[i], INPUT);
    inputs[i].gateIsHigh = readInput(i);
    inputs[i].lastChange = 0;
    inputs[i].noteIsOn = false;
    inputs[i].noteOnTime = 0;
    inputs[i].noteOffPending = false;
  }

  if (printBpm) {
    Serial.begin(115200);
  }

  // the name must be set before USB.begin():
  USB.productName(deviceName);
  MIDI.begin();
  USB.begin();
}

void loop() {
  unsigned long nowMicros = micros();
  unsigned long nowMillis = millis();

  updateInputs(nowMicros, nowMillis);
  if (useClockInput) {
    updateClock(nowMicros);
  }

  readMidi(nowMillis);
  updateOutputs(nowMillis);
}


// ---------- inputs ----------

bool readInput(int i) {
  bool pinIsHigh = digitalRead(inputPins[i]);
  return inputInverted ? !pinIsHigh : pinIsHigh;
}

void updateInputs(unsigned long nowMicros, unsigned long nowMillis) {
  for (int i = 0; i < numInputs; i++) {
    bool gate = readInput(i);
    bool isClockJack = useClockInput && (i == clockJack);
    bool sendsNote = !isClockJack || clockSendsNote;

    // the gate changed (and not too fast):
    if (gate != inputs[i].gateIsHigh && nowMicros - inputs[i].lastChange >= debounceTime) {
      inputs[i].gateIsHigh = gate;
      inputs[i].lastChange = nowMicros;

      if (gate) {
        if (isClockJack) {
          onClockPulse(nowMicros);
        }
        if (sendsNote) {
          if (inputs[i].noteIsOn) {
            sendNoteOff(inputNotes[i], inputChannel);
          }
          sendNoteOn(inputNotes[i], inputVelocity, inputChannel);
          inputs[i].noteIsOn = true;
          inputs[i].noteOnTime = nowMillis;
          inputs[i].noteOffPending = false;
        }
      } else {
        inputs[i].noteOffPending = true;
      }
    }

    // send the Note Off once the note is at least minNoteLength long:
    if (inputs[i].noteOffPending && inputs[i].noteIsOn && nowMillis - inputs[i].noteOnTime >= minNoteLength) {
      sendNoteOff(inputNotes[i], inputChannel);
      inputs[i].noteIsOn = false;
      inputs[i].noteOffPending = false;
    }
  }
}


// ---------- clock ----------
// each pulse becomes 24 / clockPulsesPerBeat MIDI clock ticks:
// one on the pulse, the rest spread evenly until the next pulse.

void onClockPulse(unsigned long nowMicros) {
  // send ticks left over from the previous pulse, so the count stays exact:
  while (ticksLeft > 0) {
    sendRealTime(midiClock);
    ticksLeft--;
  }

  if (!clockRunning) {
    clockRunning = true;
    haveInterval = false;
    pulseCount = 0;
    if (sendStartStop) {
      sendRealTime(midiStart);
    }
  } else {
    unsigned long interval = nowMicros - lastPulseTime;

    if (!haveInterval) {
      pulseInterval = interval;
      haveInterval = true;
    } else {
      // jump on big tempo changes (over 25%), smooth small ones:
      long difference = (long)interval - (long)pulseInterval;
      if (difference < 0) {
        difference = -difference;
      }
      if (difference > (long)(pulseInterval / 4)) {
        pulseInterval = interval;
      } else {
        pulseInterval = (pulseInterval * 3 + interval) / 4;
      }
    }

    bpm = 60000000.0 / ((float)pulseInterval * clockPulsesPerBeat);
  }

  lastPulseTime = nowMicros;
  pulseCount++;

  sendRealTime(midiClock);
  tickInterval = pulseInterval / ticksPerPulse;
  ticksLeft = ticksPerPulse - 1;
  nextTickTime = nowMicros + tickInterval;

  if (printBpm && haveInterval && pulseCount % clockPulsesPerBeat == 0) {
    Serial.print("BPM: ");
    Serial.println(bpm, 1);
  }
}

void updateClock(unsigned long nowMicros) {
  if (!clockRunning) {
    return;
  }

  if (ticksLeft > 0 && (long)(nowMicros - nextTickTime) >= 0) {
    sendRealTime(midiClock);
    ticksLeft--;
    nextTickTime += tickInterval;
  }

  if (nowMicros - lastPulseTime > clockTimeout * 1000UL) {
    clockRunning = false;
    ticksLeft = 0;
    if (sendStartStop) {
      sendRealTime(midiStop);
    }
    if (printBpm) {
      Serial.println("Clock stopped");
    }
  }
}


// ---------- outputs ----------

void setOutput(int i, bool high) {
  bool pinLevel = outputInverted ? !high : high;
  digitalWrite(outputPins[i], pinLevel ? HIGH : LOW);
}

void allOutputsLow() {
  for (int i = 0; i < numOutputs; i++) {
    setOutput(i, false);
    outputs[i].triggerRunning = false;
  }
}

void handleNoteOn(byte note, unsigned long nowMillis) {
  for (int i = 0; i < numOutputs; i++) {
    if (outputNotes[i] == note) {
      setOutput(i, true);
      if (outputModes[i] == TRIGGER_MODE) {
        outputs[i].triggerRunning = true;
        outputs[i].triggerEnd = nowMillis + triggerLength;
      }
    }
  }
}

void handleNoteOff(byte note) {
  for (int i = 0; i < numOutputs; i++) {
    if (outputNotes[i] == note && outputModes[i] == GATE_MODE) {
      setOutput(i, false);
    }
  }
}

void readMidi(unsigned long nowMillis) {
  midiEventPacket_t packet;

  while (MIDI.readPacket(&packet)) {
    byte messageType = packet.byte1 & 0xF0;
    byte channel = packet.byte1 & 0x0F;

    if (messageType < 0x80 || messageType >= 0xF0 || channel != outputChannel) {
      continue;
    }

    byte data1 = packet.byte2;
    byte data2 = packet.byte3;

    if (messageType == 0x90 && data2 > 0) {
      handleNoteOn(data1, nowMillis);
    } else if (messageType == 0x80 || (messageType == 0x90 && data2 == 0)) {
      handleNoteOff(data1);   // Note On with velocity 0 also means Note Off
    } else if (messageType == 0xB0 && (data1 == 123 || data1 == 120)) {
      allOutputsLow();        // All Notes Off / All Sound Off
    }
  }
}

void updateOutputs(unsigned long nowMillis) {
  for (int i = 0; i < numOutputs; i++) {
    if (outputs[i].triggerRunning && (long)(nowMillis - outputs[i].triggerEnd) >= 0) {
      setOutput(i, false);
      outputs[i].triggerRunning = false;
    }
  }
}


// ---------- MIDI messages ----------
// USB MIDI packet: [packet type] [status + channel] [data 1] [data 2]

void sendNoteOn(byte note, byte velocity, byte channel) {
  midiEventPacket_t packet = { 0x09, (byte)(0x90 | (channel & 0x0F)), note, velocity };
  MIDI.writePacket(&packet);
}

void sendNoteOff(byte note, byte channel) {
  midiEventPacket_t packet = { 0x08, (byte)(0x80 | (channel & 0x0F)), note, 0 };
  MIDI.writePacket(&packet);
}

void sendRealTime(byte message) {
  midiEventPacket_t packet = { 0x0F, message, 0, 0 };
  MIDI.writePacket(&packet);
}
