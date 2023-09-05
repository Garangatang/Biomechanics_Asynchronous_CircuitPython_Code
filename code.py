# This code is for 
# ----------------------------------------------------------------
import time

# Import the board-specific input/output library.
import board
#import digitalio
import os
import asyncio
import gc
from adafruit_bus_device import i2c_device

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_bus_device.i2c_device import I2CDevice
import adafruit_pcf8563
from adafruit_datetime import datetime

# Memory on the 
#sys.path.append("/sd")
#from MountSDCard import *

from CircularQueue import *
from ZSC31014_read import *
#from RGB_LED import *
import adafruit_rgbled
from PeakExtr import *

# Enabling garbage collection
gc.enable()

# Setting up LEDs on board
RED_LED = board.RED_LED
GREEN_LED = board.GREEN_LED
BLUE_LED = board.BLUE_LED

# Create a RGB LED object
led = adafruit_rgbled.RGBLED(RED_LED, GREEN_LED, BLUE_LED)
try:
    import MountSDCard
except Exception as e:
    print(e)
    #led.color = led.color = (0, 255, 255)
# ----------------------------------------------------------------
# Initialize global variables for the main loop.


# Setting up variables for the BLE
ble = BLERadio()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)

i2c = board.I2C()
# Setting up I2C lines for the zsc and the variables for the zsc received data
_BRIDGE_DATA_MASK = (0b1 << 14) - 1

zsc0x01_data = 0
zsc0x02_data = 0
zsc0x03_data = 0

i2c_device1 = None
i2c_device2 = None
i2c_device3 = None

current_time_stamp = ''

# If a sensor doesn't initilize the first time, the device will try
# twenty more times to initialize it before it sets the sensor value
# to -20

for x in range(0, 20):
    try:
        i2c_device1 = i2c_device.I2CDevice(i2c, 0x01)
        #print("issue")
        break
    except:
        # TODO Add sensor error logging here later
        if (x < 19):
            time.sleep(0.1)
            continue
        else:
            print("failed to initialize 0x01")
            zsc0x01_data = -20
            break

for x in range(0, 20):
    try:
        i2c_device2 = i2c_device.I2CDevice(i2c, 0x02)
        break
    except:
        # TODO Add sensor error logging here later
        if (x < 19):
            time.sleep(0.1)
            continue
        else:
            print("failed to initialize 0x02")
            zsc0x01_data = -20
            break

for x in range(0, 20):
    try:
        i2c_device3 = i2c_device.I2CDevice(i2c, 0x03)
        break
    except:
        # TODO Add sensor error logging here later
        if (x < 19):
            time.sleep(0.1)
            continue
        else:
            print("failed to initialize 0x03")
            zsc0x01_data = -20
            break


empty_buffer1 = bytearray(1)
empty_buffer2 = bytearray(1)
empty_buffer3 = bytearray(1)

buffer1 = bytearray(2)
buffer2 = bytearray(2)
buffer3 = bytearray(2)

# Setting up RTC
pcf8563 = adafruit_pcf8563.PCF8563(i2c)

# Flags for detecting state changes.
advertised = False
connected  = False

# The sensor sampling rate is precisely regulated using the following timer variables.
sampling_timer = 0.0
last_time = time.monotonic()
#sampling_interval = 0.10
# Test out different timing 0.0625 is baseline 16 Hz
sampling_interval = 0.06

# Initializing the circular buffer, which is sized to 3 minutes of data at 16 Hz
Q = CircularQueue(412)

sensor_data1 = 1

# Patient weight is defaulted at 100 for now
peakExtr = PeakExtr(100)

# BLE pause timer if end of file is reached.
BLE_pause_timer = 0

"""
def timeit(func):
    def wrapper()
        t = time()
        func()
        print(time() -t)
    return wrapper
@timeit
def write_to_sd()
    pass
""" 

# Checking if last_index file exists, and adding first value
# of zero to the file if it doesn't exist
file_list = os.listdir("/sd/")
last_index_check = "last_index.txt"

if last_index_check not in file_list:
    with open("/sd/last_index.txt", "a") as last_ind_file:
        first_index = 0
        last_ind_file.write("{}\n".format(first_index))

loading_data_check = "loading_data.txt"
if loading_data_check not in file_list:
    led.color = (0, 255, 255)
    with open("/sd/loading_data.txt", "a") as loading_data_file:
        # Just initializing file, may add a header later
        first_index = 0
        loading_data_file.write("{}\n".format(first_index))
        
peak_det_save_check = "peak_det_save.txt"
if peak_det_save_check not in file_list:
    with open("/sd/peak_det_save.txt", "a") as peak_det_save_file:
        first_peak = 0
        peak_det_save_file.write("{}\n".format(first_peak))
        

# ----------------------------------------------------------------
# Begin the main processing loop.
async def sampling_ZSC_and_write_to_sd():
    global zsc0x01_data
    global zsc0x02_data
    global zsc0x03_data
    global i2c
    
    #led.color = (255, 0, 255)
    
    while True:
        start_time = time.monotonic_ns()
        
        led.color = (255, 0, 255)
        #rgb_led(board, 255, 0, 255)
        
        # Read the accelerometer at regular intervals.  Measure elapsed time and
        # wait until the update timer has elapsed.
        now = time.monotonic()
        global last_time
        interval = now - last_time
        last_time = now
        global sampling_timer
        sampling_timer -= interval
        
        # Sampling data
        if sampling_timer < 0.0:
            global sensor_data1
            sensor_data1 = 1
            # If constant zeros are being read for a sensor
            # then it is likely broken
            # If negative values are being read, then the sensor
            # broke on initialization
            # Loading value in pounds is sensor_data * 250 / 2^14
            #global zsc0x01_data
            
            # Reading in the empty buffer first
            if zsc0x01_data != -20:
                try:
                    with i2c_device1 as i2c1:
                        i2c1.readinto(empty_buffer1)
                except Exception as e:
                    print(e)
                    print("0x01")
                    zsc0x01_data = -45
            
            if zsc0x02_data != -20:
                try:
                    with i2c_device2 as i2c2:
                        i2c2.readinto(empty_buffer2)
                except Exception as e:
                    print(e)
                    print("0x02")
                    zsc0x02_data = -45
            
            
            if zsc0x03_data != -20:
                try:
                    with i2c_device3 as i2c3:
                        i2c3.readinto(empty_buffer3)
                except Exception as e:
                    print(e)
                    print("0x03")
                    zsc0x03_data = -45
                  
            # Necessary delay after waking up the sensor before requesting data
            time.sleep(0.014)
            
            if zsc0x01_data != -20:
                try:
                    with i2c_device1 as i2c1:
                        i2c1.readinto(buffer1)
                except Exception as e:
                    print(e)
                    print("0x01")
                    zsc0x01_data = -45
            
            if zsc0x02_data != -20:
                try:
                    with i2c_device2 as i2c2:
                        i2c2.readinto(buffer2)
                except Exception as e:
                    print(e)
                    print("0x02")
                    zsc0x02_data = -45
            
            
            if zsc0x03_data != -20:
                try:
                    with i2c_device3 as i2c3:
                        i2c3.readinto(buffer3)
                except Exception as e:
                    print(e)
                    print("0x03")
                    zsc0x03_data = -45
            
            data1 = zsc0x01_data
            if zsc0x01_data != -20 and zsc0x01_data != -45:
                zsc0x01_data = int.from_bytes(buffer1, 'big')
                bridge_data1 = struct.unpack('>H', buffer1)
                data1 = bridge_data1[0]
                data1 &= _BRIDGE_DATA_MASK
            
            data2 = zsc0x02_data
            if zsc0x02_data != -20 and zsc0x02_data != -45:
                zsc0x02_data = int.from_bytes(buffer2, 'little')
                bridge_data2 = struct.unpack('>H', buffer2)
                data2 = bridge_data2[0]
                data2 &= _BRIDGE_DATA_MASK
                
            data3 = zsc0x03_data
            if zsc0x03_data != -20 and zsc0x03_data != -45:
                zsc0x03_data = int.from_bytes(buffer3, 'big')
                bridge_data3 = struct.unpack('>H', buffer3)
                data3 = bridge_data3[0]
                data3 &= _BRIDGE_DATA_MASK
                
            
            # time the samples were taken from the zsc
            current_time = 0
            if (Q.size <= 1):
                current = pcf8563.datetime
                global current_time_stamp
                # Formatting current time according to ISO 8601 
                current_time = datetime(*current[:6]).isoformat()
                current_time_stamp = current_time
                
            else:
                current_time = 0
                
                
            # Adding values to the circular buffer
            read_val_arr = [data1*250/2**14, data2*250/2**14, data3*250/2**14, current_time]
            
            if not Q.is_full():
                Q.enqueue(read_val_arr)

            # Dumping data from the circular buffer to the sd card.
            if Q.size >= 400:
                print("Current Available Memory")
                print(gc.mem_free())
                print("Q size1: ", Q.size)
                file_list = os.listdir("/sd/")
                loading_data_check = "loading_data.txt"

                try:
                    check_queue = Q.show_queue_list()
                    print("check_queue first value")
                    check_queue_date = check_queue[0]
                    global current_time_stamp
                    # Running PeakExtr first to save values to be broadcasted
                    # later via bluetooth, default pw of 100 for now
                    peakExtr.peak_extr(check_queue, current_time_stamp)
                except Exception as e:
                    print("Line 342")
                    print(e)
                    
                try:
                    if loading_data_check not in file_list:
                        led.color = (0, 255, 255)
                        time.sleep(5)
                        print("Breaking loop")
                        raise RuntimeError('SD Card disconnected')
                        break
                        
                    else:
              
                        with open("/sd/loading_data.txt", "a") as loading_file:
                            for x in range(0, Q.size):
                                stringed_arr = '\t'.join(map(str, Q.dequeue()))
                                #print(stringed_arr)
                                loading_file.write(stringed_arr + "\n")
                    
                    print("Q size2: ", Q.size)
                    print("Current Available Memory")
                    print(gc.mem_free())
                except Exception as e:
                    print("File error")
                    print(e)
        
        # Check for bluetooth to ensure new data has come in
        else:
            sensor_data1 = None
        
        end_time = time.monotonic_ns()
        #print("<= Elapsed time loading 1 =>")
        #print((end_time - start_time)/10**9)
        
        await asyncio.sleep(0.030)
        end_time = time.monotonic_ns()
        #print("<= Elapsed time loading 2 =>")
        #print((end_time - start_time)/10**9)

        
async def bluetooth_connect_and_broadcast(sensor_data1):
    while True:
        global BLE_pause_timer
        start_time = time.monotonic_ns()
        try:
            # Used to pause transmission and acquire new loading values if all previous values have been transmitted
            now = int(time.monotonic())
            time_diff = now - BLE_pause_timer
            #print("TIME DIFF")
            #print(time_diff)
            # Use asyncio to have this bluetooth function track the
            # number of lines being sent, but also have it within the 16 Hz time
            # block, so as much data can be transmitted within the 16 Hz time window
            # and if the time window closes then go back to collecting data
            # Advertising and connecting the bluetooth
            global ble
            global advertised
            #global ble
            if not advertised:
                ble.start_advertising(advertisement)
                print("Waiting for connection.")
                advertised = True
            
            global connected

            if not connected and ble.connected:
                print("Connection received.")
                connected = True
                #led.value = False
            
            # For preserving sampling rate
            await asyncio.sleep(0.0)
            
            # Wait to transmit data for 60 seconds
            if connected and time_diff >= 60:
                if not ble.connected:
                    print("Connection lost.")
                    connected = False
                    advertised = False
                else:
                    #print("Sensor data1: ", sensor_data1)
                    if sensor_data1 is not None:
                        last_broadcast_index = 0
                        with open("/sd/last_index.txt", "r") as f1:
                            print("Line 429")
                            last_broadcast_index = int(f1.readline())
                            print("Successfully read data, 431")
                        
                        with open("/sd/peak_det_save.txt", "r") as f2:
                            #while True:
                            try:
                                # Broadcasting three thousand values is
                                # based on timing for sampling from the sd card
                                for x in range(0, 3000):
                                    
                                    if ble.connected and advertised:
                                        led.color = (255, 0, 0)
                                        f2.seek(last_broadcast_index)

                                        curr_file_line1 = f2.readline()
                                        last_broadcast_index += len(curr_file_line1.encode("utf8"))

                                        string_split1 = [x.strip() for x in curr_file_line1.split('\t')]
                                        
                                        json_format_transmission1 = {"time_stamp": string_split1[0], "loading_data": string_split1[1]}
                                        
                                        json_string1 = str(json_format_transmission1)
                                        uart.write(json_string1 + "\n")
                                        print("transmitting")
                                        # awaiting once every broadcast cycle checks if sleep is done on
                                        # the sampling loop, and goes back to sample if it is.
                                        await asyncio.sleep(0)
                                    
                                    # If bluetooth is disconnected then cease any broadcasting
                                    # and record the last broadcasted line.
                                    else:
                                        f2.seek(last_broadcast_index)
                                        curr_file_line = f2.readline()
                                        print("Last broadcasted value")
                                        print(curr_file_line)
                                        break
                                
                                print("Finished broadcast burst") 
                            except Exception as e:
                                BLE_pause_timer = int(time.monotonic())
                                print("***************Line 446********************")
                                print(e)
                                # For hitting the end of file, or bluetooth error
                                # occurring 
                                print("Error in transmitting")
                                #await asyncio.sleep(0)
                                pass
                                
                        # See if possible to do a persistent write to eeprom
                        with open("/sd/last_index.txt", "w") as f1:
                            f1.write("{}\n".format(last_broadcast_index))
                        
            #gc.collect()
            #global sampling_timer
            #if sampling_timer < 0.0:
            #    sampling_timer += sampling_interval
            #print("Made it out of the loop")
            
        
        except Exception as e:
            BLE_pause_timer = int(time.monotonic())
            print(e)
            print("*******************Bluetooth encountered an error.*************************")
        
        finally:
            # Keeping consistent timing in between functions to ensure
            # there aren't any samples being dropped.
            global sampling_timer
            if sampling_timer < 0.0:
                sampling_timer += sampling_interval
            #with open("/sd/last_index.txt", "w") as f1:
            #    f1.write("{}\n".format(last_broadcast_index))
            gc.collect()
            #await asyncio.sleep(0.01)
            #continue
        
        end_time = time.monotonic_ns()
        #print("<= Elapsed time blue=>")
        #print((end_time - start_time)/10**9)
        await asyncio.sleep(0.0)

async def main():
    while True:
        try:
            # Primary task is sampling from the sensor and saving to the sd card
            sample_sensor = asyncio.create_task(sampling_ZSC_and_write_to_sd())
            
            global sensor_data1
            # Secondary task is checking for bluetooth connections and broadcasting
            # backlogged values from the sd card
            bluetooth_broadcast = asyncio.create_task(bluetooth_connect_and_broadcast(sensor_data1))
            await asyncio.gather(sample_sensor, bluetooth_broadcast)
                
        except Exception as e:
            print("In here")
            print(e)
            led.color = (0, 255, 255)
            time.sleep(5)
            pass
            
        #break

asyncio.run(main())

