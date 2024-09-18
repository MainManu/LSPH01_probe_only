import time
from tqdm import trange
from functools import partial
from .directProbeAccess import probeAccess
from .log_utils import print_data

def print_time_for_n_minutes(minutes):
    for i in trange(minutes*60):
        time.sleep(1)

            
print_time_for_24_hours = partial(print_time_for_n_minutes, minutes=24*60)

def calibration_run(probes: list[probeAccess], value):
    '''
    safe calibration, takes 24 hours
    '''
    input("please verify all probes are working using the log below(enter to show)")
    for probe in probes:
        response = probe.get_ph_high_res()
        print_data(response, probe.name)
    input('Press enter to start calibration')
    print_time_for_24_hours()
    for probe in probes:
        probe.calibrate_ph(value)

def calibration_after_n_minutes(probes, value, minutes):
    '''
    safe calibration, takes 24 hours
    '''
    input("please verify all probes are working using the log below(enter to show)")
    for probe in probes:
        response = probe.get_ph_high_res()
        print_data(response, probe.name)
    print("pleas plug the SET pins (white cable) of all probes into 5V (red cable)")
    input('Press enter to start calibration')
    print_time_for_n_minutes(minutes)
    for probe in probes:
        probe.calibrate_ph(value)
    input("please plug the SET pin back into ground (black/blue calbe)")

def instant_calibration(probes, value):
    '''
    warning: only use if probes have been in the calibration solution for a long time
    '''
    for probe in probes:
        probe.calibrate_ph(value)