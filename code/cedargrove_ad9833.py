# SPDX-FileCopyrightText: Copyright (c) 2022 JG for Cedar Grove Maker Studios
#
# SPDX-License-Identifier: MIT
"""
`cedargrove_ad9833`
================================================================================

A CircuitPython driver for the AD9833 Waveform Generator.

* Author(s): JG

Implementation Notes
--------------------

**Hardware:**

* Cedar Grove Studios AD9833 Precision Waveform Generator FeatherWing
* Cedar Grove Studios AD9833 ADSR Precision Waveform Generator FeatherWing

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""

import board
import busio
import digitalio
from adafruit_bus_device.spi_device import SPIDevice

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/CedarGroveStudios/CircuitPython_AD9833.git"


class AD9833:
    """The driver class to support the AD9833 Programmable Waveform Generator.

    The AD9833 is a programmable waveform generator that produces sine, square,
    and triangular waveform output from 0 MHz to 12.5MHz with 28-bit resolution.
    The CircuitPython SPI driver sets the waveform generator's frequency,
    phase, and waveform type properties as well as providing methods for
    resetting, starting, pausing, and stopping the generator."""

    def __init__(
        self,
        wave_freq=440,
        wave_phase=0,
        wave_type="sine",
        select="D6",
        m_clock=25000000,
    ):
        """Initialize SPI bus interconnect, derive chip select pin (to allow
        multiple class instances), and create the SPIDevice instance."""

        self._spi = busio.SPI(board.SCK, MOSI=board.MOSI)  # Define SPI bus
        self._cs = digitalio.DigitalInOut(getattr(board, select))
        self._device = SPIDevice(
            self._spi, self._cs, baudrate=5000000, polarity=1, phase=0
        )

        self._wave_freq = wave_freq
        self._wave_phase = wave_phase
        self._wave_type = wave_type

        # Initiate register contents
        self._freq_reg = 0
        self._phase_reg = 0

        # Enable initial reset state
        self._reset = True

        # Set the master clock frequency
        self._m_clock = m_clock

    @property
    def wave_freq(self):
        """The wave generator's floating or integer output frequency value.
        Default is 440Hz. Maximum is 0.5 * m_clock."""

        return self._wave_freq

    @wave_freq.setter
    def wave_freq(self, new_wave_freq=440):
        self._wave_freq = new_wave_freq
        if self._wave_freq < 0:
            self._wave_freq = 0
        if self._wave_freq > (self._m_clock // 2):
            self._wave_freq = self._m_clock // 2

    @property
    def wave_phase(self):
        """The wave generator's integer output phase value. Range is 0 to 4095
        (equivalent to 2*PI radians). Default is 0."""

        return self._wave_freq

    @wave_phase.setter
    def wave_phase(self, new_wave_phase=0):
        self._wave_phase = int(new_wave_phase)
        if self._wave_phase < 0:
            self._wave_phase = 0
        if self._wave_phase > 4095:
            self._wave_phase = 4095

    @property
    def wave_type(self):
        """The wave generator's string waveform type value. Default is "sine".
        Valid choices are "sine", "triangle", and "square"."""

        return self._wave_type

    @wave_type.setter
    def wave_type(self, new_wave_type="sine"):
        self._wave_type = new_wave_type
        if self._wave_type != "triangle" and self._wave_type != "square":
            self._wave_type = "sine"

    def _send_data(self, data):
        """Send a 16-bit word through SPI bus as two 8-bit bytes."""

        tx_msb = data >> 8
        tx_lsb = data & 0xFF

        with self._device:
            self._spi.write(bytes([tx_msb, tx_lsb]))

    def _calc_freq(self, freq=440, phase=0):
        """Convert frequency to clock divisor value and overlay frequency and
        phase register addresses. Frequency setting defaults to 440Hz, phase value
        defaults to 0 radians. Master clock is set to a default value of 25MHz.
        Register addresses default to freq_reg_0 and phase_reg_0. The function
        returns the clock divisor's Most Significant Word (MSW), Least
        Significant Word, and the phase value, addressed for the specified
        register."""

        freq_word = int(round(float(freq * pow(2, 28)) / self._m_clock))

        # Split frequency word into two 14-bit parts; MSW and LSW
        freq_msw = (freq_word & 0xFFFC000) >> 14
        freq_lsw = freq_word & 0x3FFF

        if self._freq_reg == 0:
            # bit-or freq register 0 select (DB15 = 0, DB14 = 1)
            freq_lsw |= 0x4000
            freq_msw |= 0x4000
        else:
            # bit-or freq register 1 select (DB15 = 1, DB14 = 0)
            freq_lsw |= 0x8000
            freq_msw |= 0x8000

        if self._phase_reg == 0:
            # bit-or phase register 0 select (DB15=1, DB14=1, DB13=0)
            phase |= 0xC000
        else:
            # bit-or phase register 1 select (DB15=1, DB14=1, DB13=1)
            phase |= 0xE000

        return (freq_msw, freq_lsw, phase)

    def pause(self):
        """Pause the wave generator and freeze the output at the latest voltage
        level by stopping the internal clock."""

        self._pause = True
        self._update_control_register()

    def start(self):
        """Start the wave generator with current register contents, register
        selection and wave mode setting."""

        self._reset = False  # Clear the reset bit
        self._pause = False  # Clear the clock disable bit
        self._update_control_register()

    def stop(self):
        """Stop the wave generator and reset the output to the midpoint
        voltage level."""

        self._pause = True
        self.update_phase(0)  # Set active phase register to 0
        self.update_phase(0)  # Set next phase register to 0
        self._update_control_register()

    def update_freq(self, freq=440):
        """Load the currently inactive freq_reg then make it active."""

        if self._freq_reg == 0:
            # Indicate inactive register
            self._freq_reg = 1
        else:
            self._freq_reg = 0

        freq_msw, freq_lsw, phase_word = self._calc_freq(freq)
        self._send_data(freq_lsw)  # Load new LSW into inactive register
        self._send_data(freq_msw)  # Load new MSW into inactive register

        self._update_control_register()

    def update_phase(self, ph=0):
        """Load the currently unselected phase_reg then make it active."""

        if self._phase_reg == 0:
            # Indicate inactive register
            self._phase_reg = 1
        else:
            self._phase_reg = 0

        freq_msw, freq_lsw, phase_word = self._calc_freq(phase=ph)
        self._send_data(phase_word)
        self._update_control_register()

    def reset(self, freq=440, ph=0):
        """Stop and reset the waveform generator. Pause the master clock.
        Update all registers with default values. Set sine wave mode. Clear the
        reset mode but keep the master clock paused."""

        # Set default control register settings
        self._reset = True
        self._pause = True
        self._freq_reg = 0
        self._freq_reg = 0
        self._wave_mode = "sine"
        self._update_control_register()

        # Set value registers to default values
        self.update_freq(freq)  # load freq register 0
        self.update_freq(freq)  # load freq register 1
        self.update_phase(ph)  # load phase register 0
        self.update_phase(ph)  # load phase register 1

        # Take the waveform generator out of reset state, master clock still paused
        self._reset = False
        self._update_control_register()

    def _update_control_register(self):
        """Construct the control register contents per existing local parameters
        then send the new control register word to the waveform generator."""

        # Set default control register mask value (sine wave mode)
        control_reg = 0x2000

        if self._reset:
            # Set the reset bit
            control_reg |= 0x0100

        if self._pause:
            # Disable master clock bit
            control_reg |= 0x0080

        control_reg |= self._freq_reg << 11  # Frequency register select bit
        control_reg |= self._phase_reg << 10  # Phase register select bit

        if self._wave_type == "triangle":
            # Set triangle mode
            control_reg |= 0x0002

        if self._wave_type == "square":
            # Set square mode
            control_reg |= 0x0028

        self._send_data(control_reg)
