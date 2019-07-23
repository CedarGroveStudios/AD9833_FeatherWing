# AD9833_FeatherWing_sweep_v01.py
# 2019-07-22 Cedar Grove Studios
# Fixed or swept frequency generator example. Update "initial parameters"
# section for required functionality.
# Tested on an Adafruit Feather M4 Express using CircuitPython 4.1.0 rc-1.

import time
import board
import busio
import digitalio

cs = digitalio.DigitalInOut(board.D6)
cs.direction = digitalio.Direction.OUTPUT
cs.value = True

spi = busio.SPI(board.SCK, MOSI=board.MOSI)

# Calculate frequency and form 14-bit least significant
#   and most significant words for 28-bit clock divider
#   Format 12-bit phase word
#   Default clock speed is 25MHz
def calc_wave_gen_freq(freq=440, phase=0, m_clock=25000000, freq_reg=0, phase_reg=0):
    freq_word = int(round(float(freq * pow(2,28)) / m_clock))

    # frequency word divide to two 14-bit parts as MSB and LSB.
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

def reset_wave_gen(freq=440, phase=0):  # reset wave generator with default values
    send_data(0x2100)  # reset control register
    # load freq register 0 and phase register 0
    freq_msw, freq_lsw, phase = calc_wave_gen_freq(freq, freq_reg=0, phase_reg=0)
    send_data(phase)
    send_data(freq_lsw)
    send_data(freq_msw)
    # load freq register 1 and phase register 1
    freq_msw, freq_lsw, phase = calc_wave_gen_freq(freq, freq_reg=1, phase_reg=1)
    send_data(phase)
    send_data(freq_lsw)
    send_data(freq_msw)

def update_freq(freq=440, reg=0):  # update freq register value
    freq_msw, freq_lsw, phase = calc_wave_gen_freq(freq, freq_reg=reg)
    send_data(freq_lsw)
    send_data(freq_msw)

def update_freq_reg(reg=0):  # enables frequency register
    send_data(0x2000 | reg << 11)

def start_wave_gen(type="sine"):
    control_register = 0x2000  # default sine mode
    if type == "triangle":
        control_register |= 0x0002  # triangle mode
    if type == "square":
        control_register |= 0x0028  # square mode
    send_data(control_register)  # start wave generator, sine output

def send_data(input):  # send 16-bit word through SPI bus as two 8-bit bytes
    tx_msb = input >> 8
    tx_lsb = input & 0xFF
    spi.write(bytes([tx_msb, tx_lsb]))

def pause_wave_gen():  # freeze output by stopping the internal clock
    send_data(0x2080)

# Initial parameters
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
        start_wave_gen(wave_type)

        if freq_mode == "sweep":
            old_freq = begin_freq
            f_reg = 0
            for i in range(begin_freq, end_freq, inc_freq):
                # print("sweep: frequency =", i)
                update_freq(i, f_reg)
                update_freq_reg(f_reg)

                if f_reg == 0:  # swap freq registers
                    f_reg = 1
                else:
                    f_reg = 0

                if sweep_mode == "non-linear":
                    time.sleep(periods_per_step * (1 / i))  # pause for x periods at the specified frequency
                else:
                    time.sleep(0.010)  # 10msec fixed hold time per step
        else:
            print("fixed: frequency =", begin_freq)
            update_freq(begin_freq)
            update_freq_reg()
            time.sleep(10)  # 10sec fixed hold time
        reset_wave_gen()

    finally:
        spi.unlock() # relinquish SPI bus for other uses

    time.sleep(1)  # wait a second then do it all over again
