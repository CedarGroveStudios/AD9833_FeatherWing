### _A precision waveform generator FeatherWing_
# AD9833_FeatherWing

![Image of Module](https://github.com/CedarGroveStudios/AD9833_FeatherWing/blob/master/photos/Waveform_Generator_social.png)

## Overview
The AD9833 Precision Waveform Generator FeatherWing is an Adafruit Feather-compatible module. The Waveform Generator produces an op-amp buffered sine, triangle, or square wave output with a practical frequency range of approximately 0 to 300KHz with 0.1Hz resolution.  
  * Frequency accuracy and stability is determined by the on-board 25MHz +/- 100ppm crystal oscillator (Abracon ASV-25.000MHZ-E-T).  
  * Waveform Generator control is via the Feather SPI bus; chip select is provided by the D6 GPIO pin.  
  *	Output signal peak-to-peak amplitude is adjustable with a maximum unipolar output of slightly less than 3.3 volts.  
  *	Output can optionally be connected to the A2 analog input pin via an on-board jumper for real-time output signal monitoring.  
  *	The wing derives its power from the host Feather's 3.3V power.  

The AD9833 Precision Waveform Generator FeatherWing was tested with a Feather M4 Express using CircuitPython version 4.1.0 rc-1. Example sweep generator code is provided in the repository (sweep example video: https://youtu.be/O1vMfLoCWzg). 

OSH Park project: https://oshpark.com/shared_projects/al6aPN0u

Refer to the Analog Devices' AD9833 Waveform Generator data sheet for device control protocol details.

OSH Park project: https://oshpark.com/shared_projects/al6aPN0u

![Fritzing Image](https://github.com/CedarGroveStudios/AD9833_FeatherWing/blob/master/photos/Waveform_Generator%20for%20fritzing.png)

![FeatherWing Implementation Chart](https://github.com/CedarGroveStudios/AD9833_FeatherWing/blob/master/docs/FeatherWing_Implementation_Chart.png)

## Primary Project Objectives
1)	Generate useful waveforms  
  a.	Highly accurate and stable absolute frequency: ±0.5Hz, 1000ppm  
  b.	Moderately accurate waveform shape: 8-bit minimum  
  c.	Fixed 3.0 volt peak-to-peak output, centered at 1.5 volts  
2)	Implement with CircuitPython code
3)	Increase SPI communications knowledge
4)	Improve SMD soldering skills
5)	Improve conceptual knowledge  
  a.	SPI communications  
  b.	Swept frequency control  
  c.	Digital signal generation  
  d.	CircuitPython device drivers  
  e.	ADSR envelope modulation (optional)  
6)	Fabricate physical equipment  
  a.	Workbench fixed and swept signal generator  
  b.	MIDI and CV controlled LFO and audio frequency Eurorack oscillator module  

## Deliverables
1)	Custom FeatherWing PCB, M4 Express pinout
2)	FeatherWing Implementation Chart
3)	CircuitPython device driver
4)	CircuitPython examples and test code
5)	KiCAD schematic and board layout with Gerber code
6)	OSH Park public shared project page
7)	GitHub public repository page
8)	Project description and report
9)	Workbench signal generator
10)	Eurorack module
## Concepts Learned
1)	Solder paste stencil was essential for successful SOT-23 and MSOP-10 component soldering
2)	10-bit waveform accuracy will be sufficient for most anticipated uses
3)	Waveform output amplitude was very stable from 0 to 250kHz
4)	Output buffer op-amp gain-bandwidth product limit contributes significantly to high frequency roll-off but also smooths the digital feedthrough components of the waveform
5)	The low peak of the waveform only reaches +150mV not 0V as anticipated
6)	Waveform generator DAC output filtering capacitance was listed incorrectly in the datasheet example; value used for manufacturer testing was correct
7)	Separate analog ground on the PCB helped to reduce analog output digital noise
8)	ADSR envelope generation will require additional circuitry (see AD9833_FeatherWing_ADSR repo for the full discussion of tests)
9)	Output frequency change throughput of the CircuitPython example code (using the cedargrove_AD9833 library) is approximately 450usec, allowing for frequency sweep steps and modulation rates of > 2k changes(steps) per sec
10)	CircuitPython driver code was simpler to create than anticipated  
  a.	CircuitPython SPI communications techniques are well-documented  
  b.	Command register protocol was thoroughly explained in the device datasheet  
  c.	Non-typical clock polarity was the only issue to overcome  
## Next Steps
  * Finish the ADSR envelope generation tests and incorporate additional components in the v02 PCB design
  *	Replace the existing op-amp with higher gain-bandwidth version
  *	Consider a FeatherWing-sized dual-output version
  *	Incorporate the knowledge and experience gained in this project with the design of an Arbitrary Waveform Generator FeatherWing

![Image of Test Setup](https://github.com/CedarGroveStudios/AD9833_FeatherWing/blob/master/photos/DSC05796%20combo.jpg)

