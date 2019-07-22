# AD9833_FeatherWing_sweep.py
# 2019-07-21 Cedar Grove Studios
# from https://ez.analog.com/dds/f/q-a/28431/ad9833-programming-in-raspberry-pi-using-python/332015#332015
# adapted for CircuitPython

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
def calc_wave_gen_freq(freq=440, phase=0, m_clock=25000000):
    freq_word = int(round(float(freq * pow(2,28)) / m_clock))

    # frequency word divide to two 14-bit parts as MSB and LSB.
    freq_msw = (freq_word & 0xFFFC000) >> 14
    freq_lsw = (freq_word & 0x3FFF)
    freq_lsw |= 0x4000  # select freq register 0 (DB15 = 0, DB14 = 1)
    freq_msw |= 0x4000  # select freq register 0 (DB15 = 0, DB14 = 1)
    phase |= 0xC000  # select phase register 0 (DB15=1, DB14=1)

    return(freq_msw, freq_lsw, phase)

# Reset reset_wave_gen and set default values
def reset_wave_gen(freq=440, phase=0):
    freq_msw, freq_lsw, phase = calc_wave_gen_freq(freq)
    send_data(0x2100)  # reset control register
    send_data(phase)
    send_data(freq_lsw)
    send_data(freq_msw)

def update_freq(freq=440, phase=0):
    freq_msw, freq_lsw, phase = calc_wave_gen_freq(freq)
    send_data(freq_lsw)
    send_data(freq_msw)

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

# Initial parameters
begin_freq = 20       # fixed or sweep starting frequency (Hz)
end_freq = 20000      # sweep ending frequency (Hz)
inc_freq = 100        # sweep freqency step size (Hz)
periods_per_step = 3  # number of waveform periods to hold (non-linear mode)
sweep_mode = "fixed"  # fixed or non-linear sweep hold timing
freq_mode = "sweep"   # fixed or sweep frequency
wave_type = "sine"    # sine, triangle, or square waveform

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
            for i in range(begin_freq, end_freq, inc_freq):
                print("sweep: frequency =", i)
                update_freq(i)
                if sweep_mode == "non-linear":
                    time.sleep(periods_per_step * (1 / i))  # pause for x periods at the specified frequency
                else:
                    time.sleep(0.1)  # 100msec fixed hold time per step
        else:
            print("fixed: frequency =", begin_freq)
            update_freq(begin_freq)
            time.sleep(10)  # 10sec fixed hold time

    finally:
        spi.unlock() # relinquish SPI bus for other uses

    time.sleep(1)  # wait a second then do it all over again
