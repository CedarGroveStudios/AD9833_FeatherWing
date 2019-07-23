# AD9833_FeatherWing

### _A precision waveform generator FeatherWing_

![Image of Module](https://github.com/CedarGroveStudios/AD9833_FeatherWing/blob/master/photos/Waveform_Generator%20glamour.png)

The AD9833 Precision Waveform Generator FeatherWing is an Adafruit Feather-compatible module. The Waveform Generator produces an op-amp buffered sine, triangle, or square wave output with a practical frequency range of approximately 0 to 300KHz with 0.1Hz resolution.

.  Frequency accuracy and stability is determined by the on-board 25MHz +/- 100ppm crystal oscillator (Abracon ASV-25.000MHZ-E-T). 
  
.  Waveform Generator control is via the Feather SPI bus; chip select is provided by the Feather's D6 logic pin. 
  
.  Output signal peak-to-peak amplitude is adjustable with a maximum unipolar output of slightly less than 3.3 volts. 
  
.  Output can optionally be connected to the Feather A2 analog input pin via an on-board jumper for real-time output signal monitoring.
  
.  The wing derives its power from the host Feather's 3.3V power.
  

The AD9833 Precision Waveform Generator FeatherWing was tested with a Feather M4 Express using CircuitPython version 4.1.0 rc-1. Example sweep generator code is provided in the repository. Refer to the Analog Devices' AD9833 Waveform Generator data sheet for device control protocol details.

OSH Park project: https://oshpark.com/shared_projects/al6aPN0u

![Image of Test Setup](https://github.com/CedarGroveStudios/AD9833_FeatherWing/blob/master/photos/DSC05796%20combo.jpg)
