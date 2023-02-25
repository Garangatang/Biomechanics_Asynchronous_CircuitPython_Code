# Connect to a remote sensing service over Bluetooth Low-Energy (BLE).  This
# script runs in Python 3 on a desktop or laptop.  It scans for a connection,
# the prints incoming data to the console until the connection breaks.

# It assumes the following packages have been installed:
#
#  pip3 install adafruit-blinka-bleio
#  pip3 install adafruit-circuitpython-ble

# ----------------------------------------------------------------
# Import the Adafruit Bluetooth library, part of Blinka.  Technical reference:
# https://circuitpython.readthedocs.io/projects/ble/en/latest/api.html

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

# ----------------------------------------------------------------
# Initialize global variables for the main loop.
ble = BLERadio()
uart_connection = None

# ----------------------------------------------------------------
# Begin the main processing loop.
# Incoming Bluetooth data can be malformed quite often, still working on a fix for this.
while True:
    if not uart_connection:
        print("Trying to connect...")
        for adv in ble.start_scan(ProvideServicesAdvertisement):
            if UARTService in adv.services:
                uart_connection = ble.connect(adv)
                print("Connected")
                break
        ble.stop_scan()

    if uart_connection and uart_connection.connected:
        uart_service = uart_connection[UARTService]
        while uart_connection.connected:
            print(uart_service.readline().decode("utf-8").rstrip())
