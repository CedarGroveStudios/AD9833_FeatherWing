# AD9833_FeatherWing_simple_sweep_v02.py
# 2019-07-27 Cedar Grove Studios
# Simple swept frequency generator example. Update "initial parameters"
# section for required functionality.
#
# uses cedargrove_ad9833 driver
# Tested with Adafruit Feather M4 Express and CircuitPython 4.1.0 rc-1.

import time

# establish class instance with chip_select pin D6
import cedargrove_ad9833
wave_gen = cedargrove_ad9833.AD9833(select="D6")

# *** Helpers ***

# *** Main code area ***
print("AD9833_FeatherWing_simple_sweep_v02.py")

# establish initial parameters
begin_freq = 20        # fixed or sweep starting frequency (Hz)
end_freq = 5000         # sweep ending frequency (Hz)
inc_freq = 10           # sweep freqency step size (Hz)
wave_type = "sine"      # sine, triangle, or square waveform

wave_gen.reset()  # reset and stop the wave generator; reset all registers
wave_gen.wave_type = wave_type  # load the waveform type value

while True:
    wave_gen.update_freq(begin_freq)  # set begin freq value to reduce start-up noise
    wave_gen.start()  # start the wave generator

    # sweep from begin_freq to end_freq in inc_freq steps
    for i in range(begin_freq, end_freq, inc_freq):
        wave_gen.update_freq(i)  # load the next frequency value
        time.sleep(0.010)

    wave_gen.stop()  # stop the wave generator
    time.sleep(1)  # wait a second then do it all over again
