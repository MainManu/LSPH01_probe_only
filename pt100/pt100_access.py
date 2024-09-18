# Simple demo of the MAX31865 thermocouple amplifier.
# Will print the temperature every second.
import time
import board
import busio
import digitalio
import adafruit_max31865
from typing import Any


MAX_RETRIES = 5

# Note you can optionally provide the thermocouple RTD nominal, the reference
# resistance, and the number of wires for the sensor (2 the default, 3, or 4)
# with keyword args:
#sensor = adafruit_max31865.MAX31865(spi, cs, rtd_nominal=100, ref_resistor=430.0, wires=2)
# Main loop to print the temperature every second.

class pt100_access(): 
    def __init__(self, cs_pin:Any = board.D5,  rtd_nominal: int = 100, ref_resistor: float = 430.0, wires: int = 4, dummy_temp: float= 20.0, dummy: bool = False):
        # guard clause for dummy
        self.csv_initialized = False
        if dummy == True:
            class dummy_sensor:
                def __init__(self):
                    self.temperature = dummy_temp
            self.sensor = dummy_sensor()
            return

        # Initialize SPI bus and sensor.
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        cs = digitalio.DigitalInOut(cs_pin) # Chip select of the MAX31865 board.   
        self.sensor = adafruit_max31865.MAX31865(spi, cs, rtd_nominal=rtd_nominal, ref_resistor=ref_resistor, wires=wires)


    def get_sensor_data(self)->float:
        """
        Get the temperature data from the sensor.

        Returns:
            A tuple containing the temperature data as floats.
        """
        global MAX_RETRIES
        for i in range(MAX_RETRIES):
            try:
                temperature_c = self.sensor.temperature
                return temperature_c
            except RuntimeError as e:
                if i < MAX_RETRIES - 1:
                    time.sleep(2)
                    continue
                else:
                    raise e

    def log_data(self, data: float):
        """
        Log the temperature data from the sensor.
        """
        while True:
            try:
                temperature_c = self.get_sensor_data()
                print(f"Temperature: {temperature_c} °C")
            except RuntimeError as e:
                print(f"An error occurred: {e}")
                continue
            time.sleep(1.0)
        
    def to_csv(self, data: float, path: str=f"data/pt_100{time.asctime()}.csv"):
        with open (path, "a") as file:
            if not self.csv_initialized:
                file.write("Time, Temperature\n")
                self.csv_initialized = True
            file.write(f"{time.asctime()}, {data}\n")

if __name__ == '__main__':
    pt100 = pt100_access()
    for i in range(5):
        temp = pt100.get_sensor_data(dummy_temp=20.0, dummy=True)
        pt100.log_data(temp)
        time.sleep(1)