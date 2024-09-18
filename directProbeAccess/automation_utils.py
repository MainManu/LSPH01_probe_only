from .directProbeAccess import probeAccess
from .os_utils import get_default_tty_paths, get_plugged_in_tty_paths, get_new_devices
from serial.tools import list_ports
from .exceptions import TooManyProbes

def create_n_default_path_probes(n=2, udev_setup_done=False)->list[probeAccess]:
    if udev_setup_done:
        probes = []
        for i in range(n):
            probes.append(probeAccess(f'/dev/sensor{i}', name=f'probe{i+1}'))
        return probes
    else:
        return [probeAccess(path, name=f'probe{i+1}') for i, path in enumerate(get_default_tty_paths(n_probes=n))]

def create_plugged_in_probes()->list[probeAccess]:
    return [probeAccess(port.device, name=f'probe{i+1}') for i, port in enumerate(get_plugged_in_tty_paths())]

def create_manually_named_probes() -> list[probeAccess]:
    '''
    Since probes might be located at different ports at different times, this function is used to create probes with a specific name enterd by the user
    '''

    # initialize variables
    n_probes = -1
    probes = []

    # get number of probes
    while n_probes < 1:
        try:
            n_probes = int(input('how many probes do you want to connect?'))
        except ValueError:
            print('please enter a number')

    # create probes
    old_devices = []
    while True:
        input('plug in probe and press enter')
        new_devices = get_new_devices(old_devices)
        if len(new_devices) > 1:
            raise TooManyProbes('please plug in one probe at a time')
            # raise too_many_probes('please plug in one probe at a time')
        probes.append(probeAccess(new_devices[0], name=input(f'enter name for probe {len(probes)+1}: ')))
        print(f'created {len(probes)} so far')
        old_devices = get_plugged_in_tty_paths()

        if len(probes)>=n_probes:
            break

    return probes

