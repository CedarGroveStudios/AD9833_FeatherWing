# AD9833_FeatherWing_sweep_v02.py
# 2019-07-27 Cedar Grove Studios
# Fixed or swept frequency generator example. Update "initial parameters"
# section for required functionality.
#
# uses cedargrove_ad9833 driver
# Tested with Adafruit Feather M4 Express and CircuitPython 4.1.0 rc-1.

import time

import cedargrove_ad9833
wave_gen = cedargrove_ad9833.AD9833()

# *** Helpers ***

# *** Main code area ***
print("AD9833_FeatherWing_sweep_v02.py")

# establish initial parameters
begin_freq = 20        # fixed or sweep starting frequency (Hz)
end_freq = 5000         # sweep ending frequency (Hz)
inc_freq = 10           # sweep freqency step size (Hz)
periods_per_step = 30   # number of waveform periods to hold (non-linear mode)
sweep_mode = "fixed"    # fixed (10ms per step) or non-linear sweep hold timing
freq_mode = "sweep"     # fixed or sweep frequency
wave_type = "sine"      # sine, triangle, or square waveform

while True:
    wave_gen.reset()
    wave_gen.wave_type = wave_type
    wave_gen.start()

    if freq_mode == "sweep":
        wave_gen.start()

        for i in range(begin_freq, end_freq, inc_freq):
            # print("sweep: frequency =", i)
            wave_gen.update_freq(i)

            if sweep_mode == "non-linear":
                time.sleep(periods_per_step * (1 / i))  # pause for x periods at the specified frequency
            else:
                time.sleep(0.010)  # 10msec fixed hold time per step
    else:
        # output a fixed frequency for 10 seconds
        # print("fixed: frequency =", begin_freq)
        wave_gen.update_freq(begin_freq)
        wave_gen.start()
        time.sleep(10)  # 10sec fixed hold time

    wave_gen.stop()  # stop wave generator

    time.sleep(1)  # wait a second then do it all over again
