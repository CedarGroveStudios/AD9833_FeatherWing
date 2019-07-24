# AD9833_FeatherWing_sweep_v01.py
# 2019-07-22 Cedar Grove Studios
# Fixed or swept frequency generator example. Update "initial parameters"
# section for required functionality.
#
# Tested with Adafruit Feather M4 Express and CircuitPython 4.1.0 rc-1.

import time
import board
import busio
import digitalio

cs = digitalio.DigitalInOut(board.D6)
cs.direction = digitalio.Direction.OUTPUT
cs.value = True

spi = busio.SPI(board.SCK, MOSI=board.MOSI)

# *** Helpers ***
def send_data(input):  # send 16-bit word through SPI bus as two 8-bit bytes
    tx_msb = input >> 8
    tx_lsb = input & 0xFF
    spi.write(bytes([tx_msb, tx_lsb]))

# Calculate frequency and form words for 28-bit clock divider
#   Form 12-bit phase word
#   Overlay register address
#   Default master clock frequency is 25MHz
def calc_wave_gen_freq(freq=440, phase=0, m_clock=25000000, freq_reg=0, phase_reg=0):
    freq_word = int(round(float(freq * pow(2,28)) / m_clock))

    # split frequency word into two 14-bit parts as MSW and LSW.
    freq_msw = (freq_word & 0xFFFC000) >> 14
    freq_lsw = (freq_word & 0x3FFF)
    if freq_reg == 0:  # bit-or freq register 0 select (DB15 = 0, DB14 = 1)
        freq_lsw |= 0x4000
        freq_msw |= 0x4000
    else:              # bit-or freq register 1 select (DB15 = 1, DB14 = 0)
        freq_lsw |= 0x8000
        freq_msw |= 0x8000
    if phase_reg == 0:  # bit-or phase register 0 select (DB15=1, DB14=1, DB13=0)
        phase |= 0xC000
    else:               # bit-or phase register 1 select (DB15=1, DB14=1, DB13=1)
        phase |= 0xE000

    return(freq_msw, freq_lsw, phase)

def pause_wave_gen():  # freeze output by stopping the internal clock
    send_data(0x2080)  # stop master clock and hold DAC value

def start_wave_gen(type="sine"):  # start wave generator with selected mode
    control_register = 0x2000  # default sine mode
    if type == "triangle":
        control_register |= 0x0002  # triangle mode
    if type == "square":
        control_register |= 0x0028  # square mode
    send_data(control_register)  # start wave generator, sine output

def stop_wave_gen():  # stop wave generator and hold output at mid-point
    pause_wave_gen()  # stop clock and hold DAC value
    update_phase(0,0)  # set phase register 0 to 0
    update_phase(0,1)  # set phase register 1 to 0

def select_freq_reg(reg=0, type="sine"):  # enable frequency register 0 or 1
    send_data(0x2000 | reg << 11)
    freq_register = 0x2000 | reg << 11  # default sine mode with register select bit
    if type == "triangle":
        freq_register |= 0x0002  # triangle mode
    if type == "square":
        freq_register |= 0x0028  # square mode
    send_data(freq_register)  # start wave generator, sine output

def select_phase_reg(reg=0):  # enable phase register 0 or 1 ---NOT WORKING---
    send_data()

def update_freq(freq=440, reg=0):  # update freq register value
    freq_msw, freq_lsw, phase = calc_wave_gen_freq(freq, freq_reg=reg)
    send_data(freq_lsw)
    send_data(freq_msw)

def update_phase(ph=0, reg=0):  # update freq register value
    freq_msw, freq_lsw, phase_value = calc_wave_gen_freq(phase=ph, phase_reg=reg)
    send_data(phase_value)

def reset_wave_gen(freq=440, phase=0):  # reset and stop wave generator; set default values
    send_data(0x2100)  # control register reset
    pause_wave_gen()   # stop the master clock
    # load freq register 0 and phase register 0 with default values
    update_freq(freq, 0)
    update_phase(phase, 0)
    # load freq register 1 and phase register 1 with default values
    update_freq(freq, 1)
    update_phase(phase, 1)

# *** Main code area ***
print("AD9833_FeatherWing_sweep_v01.py")

# establish initial parameters
begin_freq = 20         # fixed or sweep starting frequency (Hz)
end_freq = 20000        # sweep ending frequency (Hz)
inc_freq = 100          # sweep freqency step size (Hz)
periods_per_step = 300  # number of waveform periods to hold (non-linear mode)
sweep_mode = "fixed"    # fixed (10ms per step) or non-linear sweep hold timing
freq_mode = "sweep"     # fixed or sweep frequency
wave_type = "sine"      # sine, triangle, or square waveform

while True:
    # connect through SPI bus
    while not spi.try_lock():
        pass

    try:
        spi.configure(baudrate=1000000, phase=0, polarity=1)
        cs.value = False
        reset_wave_gen(begin_freq)

        if freq_mode == "sweep":
            # print("sweep: mode, begin, end, increment")
            # print(sweep_mode, begin_freq, end_freq, inc_freq)
            old_freq = begin_freq
            f_reg = 0
            start_wave_gen(wave_type)

            for i in range(begin_freq, end_freq, inc_freq):
                # print("sweep: frequency =", i)
                update_freq(i, f_reg)
                select_freq_reg(f_reg, wave_type)

                # alternate freq registers to eliminate register loading noise
                if f_reg == 0: f_reg = 1
                else: f_reg = 0

                if sweep_mode == "non-linear":
                    time.sleep(periods_per_step * (1 / i))  # pause for x periods at the specified frequency
                else:
                    time.sleep(0.010)  # 10msec fixed hold time per step
        else:
            # output a fixed frequency for 10 seconds
            # print("fixed: frequency =", begin_freq)
            update_freq(begin_freq)  # freq register 0
            select_freq_reg()        # freq register 0
            start_wave_gen(wave_type)
            time.sleep(10)  # 10sec fixed hold time

        stop_wave_gen()  # stop wave generator

    finally:
        spi.unlock() # relinquish SPI bus for other uses

    time.sleep(1)  # wait a second then do it all over again
