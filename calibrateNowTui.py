#! /usr/bin/env pipenv-shebang
from directProbeAccess import instant_calibration, create_n_default_path_probes, probeAccess, select_from_tty, handle_args
from directProbeAccess.modbus import parse_error, protocol_error, crc_error,empty_message_error

def main():
    probes = select_from_tty(udev_initialized=True)
    # probes = handle_args()["probes"]
    if probes == None:
        print("No probes selected")
        raise SystemExit
    # probes = [probeAccess(port='/dev/sensor1')]
    ph = int(input("enter ph value (4,7,10)"))
    # make sure the SET pins are connected to 5V (measurement returns 0)
    non_zero_value_probes = []
    while True:
        for probe in probes:
            try:
                response = probe.get_ph_high_res(ignore_errors=True)
                has_non_zero_value = response.ph_high_res != 0.0 or not response.is_empty
                if probe not in non_zero_value_probes and has_non_zero_value:
                    non_zero_value_probes.append(probe)
                elif probe in non_zero_value_probes and not has_non_zero_value:
                    non_zero_value_probes.remove(probe)
            except parse_error:
                print(f"Parse error for {probe.name}, please fix first")
            except IOError:
                print(f"IOError for {probe.name}, please fix first")
            except crc_error:
                print(f"CRC error for {probe.name}, please fix first")
            except protocol_error:
                print(f"Protocol error for {probe.name}, please fix first")
            except Exception as e:
                print(f"Error: {e} for probe {probe.name}, please fix first")
        if any(non_zero_value_probes):
            print('Please make sure the SET pins are connected to 5V')
            print(f"probes with non-zero values: {[probe.name for probe in non_zero_value_probes]}")
            input('press enter to refresh')
            continue
        else:
            break
    # ph_values = [probe.get_ph_high_res() for probe in probes]   
    # non_zero_values = [value for value in ph_values if value != 0]  
    # if non_zero_values:
    #     print('Please make sure the SET pins are connected to 5V')
    #     print('Values:', non_zero_values)
    #     return
    instant_calibration(probes, ph)
    print('Calibration finished')

if __name__ == '__main__':
    main()
