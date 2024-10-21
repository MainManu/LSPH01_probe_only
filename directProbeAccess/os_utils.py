import platform
import os
import subprocess
import time
from .exceptions import UserError
from serial.tools import list_ports

def get_default_tty_paths(n_probes=2)->list[str]:
    if platform.system() == 'Linux':
        return [f'/dev/ttyUSB{i}' for i in range(n_probes)]
    elif platform.system() == 'Darwin':
        return [f'/dev/tty.usbserial-1413{i}' for i in range(n_probes)]
    elif platform.system() == 'Windows':
        return [f'COM{i}' for i in range(n_probes)]
    else:
        raise Exception('OS not supported')

def get_plugged_in_tty_paths(udev_initialized=False)->list[str]:
    if platform.system() == 'Linux':
        if udev_initialized:
            return [f"/dev/{path}" for path in os.listdir('/dev') if 'sensor' in path]
        else:
            return [port.device for port in list_ports.grep('/dev/ttyUSB')]
    elif platform.system() == 'Darwin':
        return [port.device for port in list_ports.grep('/dev/tty.usbserial-1413')]
    elif platform.system() == 'Windows':
        return [port.device for port in list_ports.grep('COM')]

def get_new_devices(old_devices)->list[str]:
    '''
    returns a list of newly plugged in devices. If old devices is empty, returns all devices
    '''
    new_devices = get_plugged_in_tty_paths()
    if old_devices == []:
        return new_devices
    else:
        return [device for device in new_devices if device not in old_devices]

def get_device_info(device_path:str)->str:
    retry_limit = 5
    retry_counter = 0
    time.sleep(1)
    while retry_counter < retry_limit:
        try:
            device_info = subprocess.check_output(f"udevadm info --query=all --name={device_path}", shell=True).decode('utf-8')
            return device_info
        except subprocess.CalledProcessError:
            retry_counter += 1
            time.sleep(1)
    

def setup_udev_rules(export=False,dry_run=True, offset=0):
    print(f"exporting: {export}, dry_run: {dry_run}")
    old_devices = get_plugged_in_tty_paths()
    time.sleep(1)
    input('plug in known device and press enter') 
    new_devices = get_new_devices(old_devices)
    if len(new_devices) > 1:
        raise UserError('please plug in one device at a time')
    device_info = get_device_info(new_devices[0])
    device_id = [line.split('=')[1] for line in device_info.split('\n') if line.startswith('E: ID_MODEL_ID=')][0]
    vendor_id = [line.split('=')[1] for line in device_info.split('\n') if line.startswith('E: ID_VENDOR_ID=')][0]

    udev_rules = ""
    counter = offset
    last_kernels_str = ""


    while input('plug in known device into next port, q to exit') != 'q':
        new_devices = get_new_devices(old_devices)
        if len(new_devices) > 1:
            print('please plug in one device at a time')
            continue
        device_info = get_device_info(new_devices[0])
        devpath_line = [line for line in device_info.split('\n') if line.startswith('E: DEVPATH=')][0]
        kernels_str = devpath_line.split("/")[-5]
        if kernels_str == last_kernels_str:
            print('same device, skipping')
            continue
        last_kernels_str = kernels_str
        udev_rules = (f'{udev_rules}\nSUBSYSTEM=="tty", KERNELS=="{kernels_str}", SYMLINK+="sensor{counter}"')
        # udev_rules = (f'{udev_rules}\nSUBSYSTEM=="tty", ATTRS{{idVendor}}=="{vendor_id}", ATTRS{{idProduct}}=="{device_id}", KERNELS=="{kernels_str}", SYMLINK+="sensor{counter}"')
        counter += 1        
        time.sleep(1)
    
    if dry_run:
        print('================')
        print("START_UDEV_RULES")
        print(udev_rules)
        print("END_UDEV_RULES")
        print('================')
    if export:
        with open('export_udev_rules.txt', 'w') as f:
            f.write(udev_rules)
    else:
        with open('/etc/udev/rules.d/99-sensor.rules', 'w') as f:
            f.write(udev_rules)
        subprocess.run('udevadm control --reload-rules && udevadm trigger', shell=True)
