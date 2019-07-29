# AD9833_FeatherWing_MIDI_in_v00.py
# 2019-07-28 Cedar Grove Studios
# Simple MIDI voice module using Cedar Grove AD9833 Precision Waveform
#     Generator FeatherWing and Cedar Grove Classic MIDI FeatherWing
#
#      cedargrove_ad9833 driver
#      cedargrove_MIDI_util library
#
# Tested with Adafruit Feather M4 Express and CircuitPython 4.1.0 rc-1.

# establish class instance with chip_select pin D6
import cedargrove_ad9833
wave_gen = cedargrove_ad9833.AD9833(select="D6")

import board
import busio
import time
import adafruit_midi
import usb_midi
from cedargrove_MIDI_util import *

from adafruit_midi.timing_clock            import TimingClock
from adafruit_midi.channel_pressure        import ChannelPressure
from adafruit_midi.control_change          import ControlChange
from adafruit_midi.note_off                import NoteOff
from adafruit_midi.note_on                 import NoteOn
from adafruit_midi.pitch_bend              import PitchBend
from adafruit_midi.polyphonic_key_pressure import PolyphonicKeyPressure
from adafruit_midi.program_change          import ProgramChange
from adafruit_midi.start                   import Start
from adafruit_midi.stop                    import Stop
from adafruit_midi.system_exclusive        import SystemExclusive
from adafruit_midi.midi_message            import MIDIUnknownEvent

UART = busio.UART(board.TX, board.RX, baudrate=31250, timeout=0.001)
midi = adafruit_midi.MIDI(midi_in=UART, midi_out=UART, in_channel=0, out_channel=0)

# *** Helpers ***

# *** Main code area ***
print("AD9833_FeatherWing_MIDI_in_v00.py")
print("Input channel:", midi.in_channel + 1 )

# establish initial parameters
t0 = time.monotonic_ns()
tempo = 0
wave_type = "sine"      # sine, triangle, or square waveform

wave_gen.reset()  # reset and stop the wave generator; reset all registers
wave_gen.wave_type = wave_type  # load the waveform type value

while True:

    msg = midi.receive()

    if msg is not None:
        midi.send(msg)  # MIDI thru
        if isinstance(msg, NoteOn):
            print("NoteOn : #%02d %s %5.3fHz" % (msg.note, note_lexo(msg.note), note_freq(msg.note)))
            print("     vel   %03d     chan #%02d" %(msg.velocity, msg.channel + 1))
            wave_gen.update_freq(note_freq(msg.note))
            if msg.velocity > 0: wave_gen.start()
            else: wave_gen.stop()

        elif isinstance(msg, NoteOff):
            print("NoteOff: #%02d %s %5.3fHz" % (msg.note, note_lexo(msg.note), note_freq(msg.note)))
            print("     vel   %03d     chan #%02d" %(msg.velocity, msg.channel + 1))
            wave_gen.stop()

        elif isinstance(msg, TimingClock):
            t1 = time.monotonic_ns()
            tempo = (tempo + (1 / ((t1 - t0) * 24) * 60 * 1e9)) / 2 # simple running average
            if (t1-t0) != 0: print("-- Tick: %03.1f BPM" % tempo)  # compared to previous tick
            t0 = time.monotonic_ns()

        elif isinstance(msg, ChannelPressure):
            print("ChannelPressure: ")
            print("     press %03d     chan #%02d" %(msg.pressure, msg.channel + 1))
            wave_type = "sine"
            if msg.pressure > 24: wave_type = "triangle"
            if msg.pressure > 80: wave_type = "square"
            wave_gen.wave_type = wave_type
            wave_gen.start()

        elif isinstance(msg, ControlChange):
            print("ControlChange: ctrl #%03d  %s" % (msg.control, cc_decoder(msg.control)))
            print("     value %03d     chan #%02d" %(msg.value, msg.channel + 1))

        elif isinstance(msg, PitchBend):
            print("PitchBend: ")
            print("     bend  %05d   chan #%02d" %(msg.pitch_bend, msg.channel + 1))

        elif isinstance(msg, PolyphonicKeyPressure):
            print("PolyphonicKeyPressure:")
            print("          #%02d %s %5.3fHz" % (msg.note, note_lexo(msg.note), note_freq(msg.note)))
            print("     press %03d     chan #%02d" %(msg.pressure, msg.channel + 1))

        elif isinstance(msg, ProgramChange):
            print("ProgramChange:")
            print("     patch %03d     chan #%02d" %(msg.patch, msg.channel + 1))

        elif isinstance(msg, (Start, Stop)): print("-- %s --" % str(type(msg))[8:-2])

        elif isinstance(msg, SystemExclusive):
            print("SystemExclusive:  ID= ", msg.manufacturer_id,
                ", data= ", msg.data)
            print("--------------------")

        elif isinstance(msg, MIDIUnknownEvent):
            # Message are only known if they are imported
            print("Unknown MIDI event status ", msg.status)
