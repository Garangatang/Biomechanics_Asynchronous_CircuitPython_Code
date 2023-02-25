# Biomechanics_Asynchronous_Circuitpython_Code
This code is written in CircuitPython and is intended for use on a Seeeduino Xiao nrf52840 Bluetooth chip.

Its intended purpose is to sample data from a custom load measuring CAM boot walker insole developed in the Hitchcock Biomechanics lab.
Sampled data is then discretized and broadcasted via Bluetooth to an mHealth app when it connects to the microcontroller.

The Python file host_ble_receiver.py can be loaded onto any computer with Bluetooth data receiving capabilities in order to receive data
from the nrf52840 chip after it has discretized an adequate amount of data.

the lib folder contains all the CircuitPython Dependencies which need to be loaded onto the microcontroller in order for all functions to work.

This repository as is can be downloaded and all files can be uploaded directly to a Seeeduino nrf52840 microcontroller.
