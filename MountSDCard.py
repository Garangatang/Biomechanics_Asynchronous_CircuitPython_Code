# Used to instantiate the SD card and set up the SPI lines for saving or reading data

import board
import busio
import digitalio
import adafruit_sdcard
import storage

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

cs = digitalio.DigitalInOut(board.D2)
# Or use a digitalio pin like 5 for breakout wiring:

sdcard = adafruit_sdcard.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")
