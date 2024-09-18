import time


MAX_RETRIES = 5

def get_sensor_data(sensor)->tuple[float, float]:
    """
    Get the humidity and temperature data from the sensor.

    Args:
        sensor: The DHT sensor to read from.

    Returns:
        A tuple containing the humidity and temperature data as floats.
    """
    global MAX_RETRIES
    for i in range(MAX_RETRIES):
        try:
            temperature_c = sensor.temperature
            humidity = sensor.humidity
            return humidity, temperature_c
        except RuntimeError as e:
            if i < MAX_RETRIES - 1:  # i is zero indexed
                time.sleep(2)  # wait for 2 seconds before trying again
                continue
            else:
                raise e