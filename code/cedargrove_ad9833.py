# The MIT License (MIT)

# Copyright (c) 2019 Cedar Grove Studios

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`cedargrove_ad9833`
================================================================================
cedargrove_ad9833.py 2019-07-27 v00 06:59PM
A CircuitPython class for controlling the AD9833 Precision Waveform
Generator FeatherWing.

* Author(s): Cedar Grove Studios

Implementation Notes
--------------------
**Hardware:**
* Cedar Grove Studios AD9833 Precision Waveform Generator FeatherWing

**Software and Dependencies:**
* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/CedarGroveStudios/AD9833_FeatherWing.git"

class AD9833:
    """wave_generator helper class."""

    def __init__(self, wave_freq=440, wave_phase=0, wave_type="sine", select="D6", m_clock=25000000, debug=False):
        import board
        import busio
        import digitalio

        # set up SPI bus interconnect, derive chip select pin (to allow multiple
        #   WaveGenerator class instances), and create SPIDevice instance
        #   Note that the 5Mhz AD9833 clock polarity is inverted from the default
        self._spi = busio.SPI(board.SCK, MOSI=board.MOSI)  # setup SPI bus
        self._cs = digitalio.DigitalInOut(getattr(board, select))  # derive chip select pin
        from adafruit_bus_device.spi_device import SPIDevice  # initiate SPI device manager
        self._device = SPIDevice(self._spi, self._cs, baudrate=5000000, polarity=1, phase=0)

        # input parameters
        self._wave_freq = wave_freq
        self._wave_phase = wave_phase
        self._wave_type = wave_type

        # initial register addresses
        self._freq_reg = 0
        self._phase_reg = 0

        # initial reset state
        self._reset = True  # reset enabled

        # master clock
        self._m_clock = m_clock

        # debug parameters
        self._debug = debug
        if self._debug:
            print("*Init:", self.__class__)
            print("*Init: ", self.__dict__)

    @property
    def wave_freq(self):
        """The wave generator's floating or integer output frequency value.
           Default is 440Hz. Maximum is 0.5 * m_clock."""
        return self._wave_freq

    @wave_freq.setter
    def wave_freq(self, wave_freq=440):
        self._wave_freq = wave_freq
        if self._wave_freq < 0: self._wave_freq = 0
        if self._wave_freq > (self._m_clock // 2): self._wave_freq = (self._m_clock // 2)

    @property
    def wave_phase(self):
        """The wave generator's integer output phase value. Default is 0Hz.
           Maximum is 4095 (equivalent to 2*PI radians)"""
        return self._wave_freq

    @wave_phase.setter
    def wave_phase(self, wave_phase=0):
        self._wave_phase = int(wave_phase)
        if self._wave_phase < 0: self._wave_phase = 0
        if self._wave_phase > 4095: self._wave_phase = 4095

    @property
    def wave_type(self):
        """The wave generator's string waveform type value. Default is "sine".
           Valid choices are "sine", "triangle", and "square"."""
        return self._wave_type

    @wave_type.setter
    def wave_type(self, wave_type="sine"):
        self._wave_type = wave_type
        if self._wave_type != "triangle" and self._wave_type !="square":
            self._wave_type = "sine"

    def send_data(self, data):  # send 16-bit word through SPI bus as two 8-bit bytes
        tx_msb = data >> 8
        tx_lsb = data & 0xFF

        with self._device:
            self._spi.write(bytes([tx_msb, tx_lsb]))

    def calc_freq(self, freq=440, phase=0):
        """ Convert frequency to clock divisor value and overlay frequency and
        phase register addresses. Frequency setting defaults to 440Hz, phase value
        defaults to 0 radians. Master clock is set to a default value of 25MHz.
        Register addresses default to freq_reg_0 and phase_reg_0. The function
        returns the clock divisor's Most Significant and Least Significant Words and
        the phase value, addressed for the specified register.
        """
        freq_word = int(round(float(freq * pow(2,28)) / self._m_clock))

        # split frequency word into two 14-bit parts as MSW and LSW.
        freq_msw = (freq_word & 0xFFFC000) >> 14
        freq_lsw = (freq_word & 0x3FFF)
        if self._freq_reg == 0:  # bit-or freq register 0 select (DB15 = 0, DB14 = 1)
            freq_lsw |= 0x4000
            freq_msw |= 0x4000
        else:              # bit-or freq register 1 select (DB15 = 1, DB14 = 0)
            freq_lsw |= 0x8000
            freq_msw |= 0x8000
        if self._phase_reg == 0:  # bit-or phase register 0 select (DB15=1, DB14=1, DB13=0)
            phase |= 0xC000
        else:               # bit-or phase register 1 select (DB15=1, DB14=1, DB13=1)
            phase |= 0xE000

        return(freq_msw, freq_lsw, phase)

    def pause(self):  # freeze output by stopping the internal clock
        """ Pause the wave generator and freeze the output at the
            latest voltage level.
        """
        self._pause = True
        self.update_control_reg()  # send pause control reg word

    def start(self):  # start wave generator
        """ Start the wave generator with current register contents, register
            selection and wave mode setting.
        """
        self._reset = False  # clear the reset bit
        self._pause = False  # clear the clock disable bit
        self.update_control_reg()  # start wave generator

    def stop(self):  # stop wave generator and hold output at mid-point
        """ Stop the wave generator and reset the output to the midpoint
            voltage level.
        """
        self._pause = True
        self.update_phase(0)  # set active phase register to 0
        self.update_phase(0)  # set next phase register to 0
        self.update_control_reg()  # send pause control reg word

    def update_freq(self, freq=440):  # update freq register value
        """ Load the currently inactive freq reg then make it active.
        """
        if self._freq_reg == 0: self._freq_reg = 1  # indicate inactive register
        else: self._freq_reg = 0

        freq_msw, freq_lsw, phase_word = self.calc_freq(freq)
        self.send_data(freq_lsw)  # load new LSW into inactive register
        self.send_data(freq_msw)  # load new MSW into inactive retister

        self.update_control_reg()  # activate updated reg

    def update_phase(self, ph=0):  # update freq register value
        """ Load the currently unselected phase reg then make it active.
        """
        if self._phase_reg == 0: self._phase_reg = 1  # indicate inactive register
        else: self._phase_reg = 0

        freq_msw, freq_lsw, phase_word = self.calc_freq(phase=ph)
        self.send_data(phase_word)
        self.update_control_reg()  # activate updated reg

    def reset(self, freq=440, ph=0):
        """ Stop and reset the waveform generator. Pause the master clock.
            Update all registers with default values. Set sine wave mode.
            Clear the reset mode but keep the master clock paused.
        """
        # set default control register settings
        self._reset = True
        self._pause = True
        self._freq_reg = 0
        self._freq_reg = 0
        self._wave_mode = "sine"
        self.update_control_reg()  # send reset control reg word

        # set registers to default values
        self.update_freq(freq)  # load freq register 0
        self.update_freq(freq)  # load freq register 1
        self.update_phase(ph)   # load phase register 0
        self.update_phase(ph)   # load phase register 1

        # take the waveform generator out of reset mode, master clock still paused
        self._reset = False
        self.update_control_reg()

    def update_control_reg(self):
        """ Construct the control register contents per existing local parameters
            then send the new control register word to the waveform generator.
        """
        control_reg = 0x2000  # default control register skeleton value (sine wave mode)
        if self._reset : control_reg |= 0x0100  # reset bit
        if self._pause : control_reg |= 0x0080  # disable master clock bit
        control_reg |= self._freq_reg << 11  # freq register select bit
        control_reg |= self._phase_reg << 10 # phase register select bit
        if self._wave_type == "triangle":
            control_reg |= 0x0002  # triangle mode
        if self._wave_type == "square":
            control_reg |= 0x0028  # square mode
        self.send_data(control_reg)
