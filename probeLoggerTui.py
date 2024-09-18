#!/usr/bin/env pipenv-shebang
import time
import board
# import adafruit_dht
from directProbeAccess import probeAccess, insert_data, init_db, print_data, create_n_default_path_probes, create_manually_named_probes, get_plugged_in_tty_paths, select_from_tty, set_expected_ph_values, create_table, insert_data_csv
from DHT22 import to_csv, dht_access
def cleanup_probes(probes):
    if probes != None:
        for probe in probes:
            probe.close()

def main():
    
    #conn, cur = init_db()
    #create_table(conn)
    # sensor = adafruit_dht.DHT22(board.D4)
 
    try:
        # probes = create_n_default_path_probes(n=2)
        # probe1 = probeAccess('/dev/tty.usbserial-14120', name='probe1')
        # probe2 = probeAccess('/dev/tty.usbserial-141320', name='probe2')
        # probes = [probe1, probe2]
        # probes = create_manually_named_probes()
        retry_counter = 0
        # probes = create_n_default_path_probes(n=6, udev_setup_done=True)
        probes = select_from_tty(udev_initialized=True)
            
        # probes = select_from_tty()
        expected_ph = float(input("Enter expected ph value"))
        expected_ph_values_list = [expected_ph]*len(probes)
        expected_ph_values = dict(zip([probe.name for probe in probes], expected_ph_values_list))
        # expected_ph_values = set_expected_ph_values(probes)


        # make sure all probes are working
        for probe in probes:
            result = probe.init_measurement()
            insert_data_csv(result.ph_high_res, result.ph_low_res, result.temperature, name=probe.name, timestamp=time.asctime(),ph_should_be=expected_ph_values[probe.name])
            print_data(result, probe.name, expected_ph_values[probe.name])
        time.sleep(120)

        while True:
            # humidity, temperature_c = dht_access.get_sensor_data(sensor)
            # to_csv(humidity, temperature_c)
            for probe in probes:
                try:
                    response = probe.get_ph_high_res()
                    insert_data_csv(response.ph_high_res, response.ph_low_res, response.temperature, name=probe.name, timestamp=time.asctime(),ph_should_be=expected_ph_values[probe.name]) 
                    #insert_data(cur, conn, response.ph_high_res, response.ph_low_res, response.temperature, name=probe.name) 
                    print_data(response, probe.name, expected_ph_values[probe.name])
                except IOError as e:
                    print(f"IOError for {probe.name}, skipping")

            time.sleep(120)
    except KeyboardInterrupt:
        print("Keyboard interrupt")
        print("cleaning up....")
        if 'probes' in locals():
            cleanup_probes(probes) 
    finally:
        #check if probes exist and close them
        if 'probes' in locals():
            cleanup_probes(probes)
if __name__ == '__main__':
    main()
