# Complete Project Details: https://RandomNerdTutorials.com/raspberry-pi-dht11-dht22-python/
# Based on Adafruit_CircuitPython_DHT Library Example

import time
import board
import adafruit_dht
import dht_access
from log_utils import to_csv


# Sensor data pin is connected to GPIO 4
sensor = adafruit_dht.DHT22(board.D4)
# Uncomment for DHT11
#sensor = adafruit_dht.DHT11(board.D4)

while True:
    try:
        # Print the values to the serial port
        humidity, temperature_c = dht_access.get_sensor_data(sensor)
        temperature_f = temperature_c * (9 / 5) + 32
        print("Temp={0:0.1f}ºC, Temp={1:0.1f}ºF, Humidity={2:0.1f}%".format(temperature_c, temperature_f, humidity))
        to_csv(humidity, temperature_c)

    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        sensor.exit()
        raise error

    time.sleep(120)