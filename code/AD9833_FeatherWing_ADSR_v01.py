# AD9833_FeatherWing_ADSR_v01.py
# 2019-07-31 Cedar Grove Studios
# Simple MIDI voice module using Cedar Grove AD9833 Precision Waveform
#     Generator FeatherWing and Cedar Grove Classic MIDI FeatherWing
#
#      cedargrove_AD9833_FeatherWing library
#      cedargrove_MIDI_util library
#
# Tested with Adafruit Feather M4 Express and CircuitPython 4.1.0 rc-1.

# establish class instance with chip_select pin D6
import cedargrove_AD9833_FeatherWing as AD9833
wave_gen = AD9833.WaveGenerator(select="D6")

import board
import busio
import time
from math import sin
import adafruit_midi
import usb_midi

# use one of M4's DACs to control output amplitude
# connect output of AD9833 wing to Feather AREF (after removing AREF to 3.3v trace)
from analogio import AnalogOut
dac_out = AnalogOut(board.A0)
dac_out.value = 0  # mute the output

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

def amplitude_stepper(start, end, period, level=1.0, port=False, note=0, last_note=0):  # step from start to end amplitude over time period
    if start < end:
        for i in range(0, 64):
            r = (3 / 2 * 3.14159) + ((3.14159 / 64) * i)
            if port:
                wave_gen.update_freq(note_freq(last_note)+(((note_freq(note)-note_freq(last_note))/64)*i))
                amplitude = end * level
            else:
                wave_gen.update_freq(note_freq(note))
                amplitude = (start + ((end - start) * ((sin(r) + 1) / 2))) * level
            dac_out.value = int(65535 * amplitude)
            time.sleep(period / 64)
    elif start > end:
         for i in range(0, 64):
            r = (3.14159 / 2) + ((3.14159 / 64) * i)
            if port:
                wave_gen.update_freq(note_freq(last_note)+(((note_freq(note)-note_freq(last_note))/64)*i))
                amplitude = end * level
            else:
                wave_gen.update_freq(note_freq(note))
                amplitude = (end + ((start - end) * ((sin(r) + 1) / 2))) * level
            dac_out.value = int(65535 * amplitude)
            time.sleep(period / 64)
    else:  # start = end
        dac_out.value = int(65535 * start * level)
        time.sleep(period)

def wave_ADSr(a=(1.0,0), d=(1.0,0), s=(1.0,0), level=1.0, port=False, note=0, last_note=0):
    amplitude_stepper(0, a[0], a[1], level, port, note, last_note)  # attack
    amplitude_stepper(a[0], d[0], d[1], level, port, note, note)  # decay
    amplitude_stepper(d[0], s[0], s[1], level, port, note, note)  # sustain

def wave_adsR(s=(1.0,0), r=(0.0,0), level=0, port=False):
    if port: amplitude_stepper(s[0], s[0], r[1], level, port)  # release
    else: amplitude_stepper(s[0], r[0], r[1], level, port)  # release

# *** Main code area ***
print("AD9833_FeatherWing_ADSR_v01.py")
print("Input channel:", midi.in_channel + 1 )

# establish initial parameters
adsr_A  = (1.0, 0.10)  # attack level, time
adsr_D  = (0.8, 0.05)  # decay level, time
adsr_S  = (0.8, 0.05)  # sustain level, time
adsr_R  = (0.0, 0.10)  # release level, time

t0 = time.monotonic_ns()
tempo = 0.0  # establish initial tempo value
last_vel_level = 0.0  # establish initial last velocity value
last_note_value = 0  # establish initial last note value

portamento = False  # default portamento value

wave_type = "triangle"  # sine, triangle, or square waveform
wave_gen.reset()  # reset and stop the wave generator; reset all registers
wave_gen.wave_type = wave_type  # load the waveform type value
wave_gen.start()

while True:
    msg = midi.receive()

    if msg is not None:
        # midi.send(msg)  # MIDI thru
        if isinstance(msg, NoteOn):
            print("NoteOn : #%02d %s %5.3fHz" % (msg.note, note_lexo(msg.note), note_freq(msg.note)))
            print("     vel   %03d     chan #%02d" %(msg.velocity, msg.channel + 1))
            last_vel_level = msg.velocity / 127
            if msg.velocity > 0: wave_ADSr(adsr_A, adsr_D, adsr_S, msg.velocity / 127, portamento, msg.note, last_note_value)
            else: wave_adsR(adsr_S, adsr_R, last_vel_level, portamento)
            last_note_value = msg.note

        elif isinstance(msg, NoteOff):
            print("NoteOff: #%02d %s %5.3fHz" % (msg.note, note_lexo(msg.note), note_freq(msg.note)))
            print("     vel   %03d     chan #%02d" %(msg.velocity, msg.channel + 1))
            wave_adsR(adsr_S, adsr_R, last_vel_level, portamento)
            last_note_value = msg.note

        elif isinstance(msg, TimingClock):
            t1 = time.monotonic_ns()
            if (t1-t0) != 0:
                tempo = (tempo + (1 / ((t1 - t0) * 24) * 60 * 1e9)) / 2 # simple running average
                # print("-- Tick: %03.1f BPM" % tempo)  # compared to previous tick
            t0 = time.monotonic_ns()

        elif isinstance(msg, ChannelPressure):
            print("ChannelPressure: ")
            print("     press %03d     chan #%02d" %(msg.pressure, msg.channel + 1))
            '''wave_type = "sine"
            if msg.pressure > 24: wave_type = "triangle"
            if msg.pressure > 80: wave_type = "square"
            wave_gen.wave_type = wave_type
            wave_gen.start()'''

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
            
