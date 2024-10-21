import curses
import re
import time
from argparse import ArgumentParser
from .directProbeAccess import probeAccess
from .os_utils import get_plugged_in_tty_paths

def handle_args():
    ret = {
        "probes": [],
        "expected_ph_values": [],
    }
    parser = ArgumentParser(description="Directly access pH probes")
    parser.add_argument("-probe", "--probe", help="The path to a single probe", type=str)
    parser.add_argument("-start", "--start", help="the path to the first consecutive probe", type=str)
    parser.add_argument("-end", "--end", help="the path to the last consecutive probe", type=str)
    parser.add_argument("-select_ui", "--select_ui", help="Select the probes from a list of plugged in probes", action="store_true")
    parser.add_argument("-auto_refresh", "--auto_refresh", help="Automatically refresh the list of plugged in probes", action="store_true")
    parser.add_argument("-expected_ph_value", "--expected_ph_value", help="Set the expected pH value for all probes", type=float)
    parser.add_argument("-set_expected_ph_ui", "--set_expected_ph_ui", help="Set the expected pH value for all probes in a ui", action="store_true")
    parser.add_argument("-save_config", "--save_config", help="Save the configuration to a file", action="store_true")
    parser.add_argument("-udev_initialized", "--udev_initialized", help="set true if udev is already configured to map probes to /dev/sensor*", action="store_true")
    
    args = parser.parse_args()

    if args.probe:
        ret["probes"].append(probeAccess(port=args.probe))
    elif args.start and args.end:
        # match the trailing number in the start and end strings, and create a list of probeAccess objects
        start_num = int(re.search(r'\d+$', args.start).group())
        end_num = int(re.search(r'\d+$', args.end).group())
        ret.append([probeAccess(port=args.start[:-1] + str(i)) for i in range(start_num, end_num+1)])
    elif args.select_ui:
        ret["probes"] = select_from_tty(auto_refresh=args.auto_refresh, udev_initialized=args.udev_initialized)
        if args.set_expected_ph_ui:
                ret["expected_ph_values"] = set_expected_ph_values(ret["probes"])
        if args.save_config:
            save_config({probe.port: probe.name for probe in ret["probes"]}, ret["expected_ph_values"])
    if args.expected_ph_value:
        ret["expected_ph_values"] = [args.expected_ph_value] * len(ret["probes"])
    return ret
       


def select_from_tty(auto_refresh=False, udev_initialized=False):
    def select_from_tty_logic(stdscr):
        ports = get_plugged_in_tty_paths(udev_initialized=udev_initialized)
        selected = [False]*len(ports)
        pos = 0 # position of the selector
        title_offset = 2 # offset of the title

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Select the ports you want to use", curses.A_BOLD)
            stdscr.addstr(1, 0, "Navigate with arrow keys, press space to select/deselect, and press enter when done.")
            for i, port in enumerate(ports):
                if i == pos:
                    stdscr.addstr(i+title_offset, 0, "> " + port + " <" + (" (selected)" if selected[i] else ""))
                else:
                    stdscr.addstr(i+title_offset, 0, "  " + port + "  " + (" (selected)" if selected[i] else ""))
            stdscr.refresh()

            key = stdscr.getch()

            if key == curses.KEY_UP and pos > 0:
                pos -= 1
            elif key == curses.KEY_DOWN and pos < len(ports)-1:
                pos += 1
            elif key == ord(' '): # space bar
                selected[pos] = not selected[pos]
            elif key == ord('\n'): # enter key
                break

        return [port for i, port in enumerate(ports) if selected[i]]

    def name_ports_with_refresh(stdscr):
        # ui to name the ports while refreshing the list of ports
        # this enables you to plug in a new probe and name it while naming the other probes
        # navigate the list with arrow keys, enter a name to name a device, 'ctl-r' to refresh the list, and 'Enter' to quit

        devices = get_plugged_in_tty_paths() 
        device_names = {device: "" for device in devices}
        pos = 0 # position of the selector
        title_offset = 2 # offset of the title

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Enter names for the devices", curses.A_BOLD) 
            stdscr.addstr(1, 0, "Navigate with arrow keys, type to rename, 'ctl-r' to refresh the list, and press enter when done.")
            for i, (device, name) in enumerate(device_names.items()):
                if i == pos:
                    stdscr.addstr(i+title_offset, 0, "> " + device + " | " + name + " <")
                else:
                    stdscr.addstr(i+title_offset, 0, "  " + device + " | " + name + "  ")
            stdscr.refresh()

            key = stdscr.getch()

            if key == curses.KEY_UP and pos > 0:
                pos -= 1
            elif key == curses.KEY_DOWN and pos < len(devices)-1:
                pos += 1
            elif key == ord('\n'):
                break
            elif key == ord('r') and curses.KEY_CTRL:
                devices = get_plugged_in_tty_paths()
                # update the device list on screen without deleting the names
                for i, device in enumerate(devices):
                    device_names[device] = device_names.get(device, "")
            elif key == curses.KEY_BACKSPACE:
                device_names[devices[pos]] = device_names[devices[pos]][:-1]
            else:
                device_names[devices[pos]] += chr(key)
            # update the device list on screen after 5 seconds
            if time.time() % 5 == 0:
                devices = get_plugged_in_tty_paths()
                for i, device in enumerate(devices):
                    device_names[device] = device_names.get(device, "")

        return device_names



    def name_ports(stdscr, selected_ports):
        names = [""]*len(selected_ports)
        pos = 0 # position of the selector
        title_offset = 2 # offset of the title
    
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Enter names for the selected ports", curses.A_BOLD) 
            stdscr.addstr(1, 0, "Navigate with arrow keys, type to rename, backspace to delete, and press enter when done.")
            for i, (port, name) in enumerate(zip(selected_ports, names)):
                if i == pos:
                    stdscr.addstr(i+title_offset, 0, "> " + port + " | " + name + " <")
                else:
                    stdscr.addstr(i+title_offset, 0, "  " + port + " | " + name + "  ")
            stdscr.refresh()
    
            key = stdscr.getch()
    
            if key == curses.KEY_UP and pos > 0:
                pos -= 1
            elif key == curses.KEY_DOWN and pos < len(selected_ports)-1:
                pos += 1
            elif key == curses.KEY_BACKSPACE:
                names[pos] = names[pos][:-1]
            elif key == ord('\n'): # enter key
                break
            else:
                names[pos] += chr(key)
    
        return dict(zip(selected_ports, names))    

    if auto_refresh == True:
        paths_with_names =  curses.wrapper(name_ports_with_refresh)
        return [probeAccess(port=port, name=name) for port,name in paths_with_names.items()]
    paths =  curses.wrapper(select_from_tty_logic)
    named_ports = curses.wrapper(name_ports, paths)
    print(named_ports)
    return [probeAccess(port=port, name=name) for port,name in named_ports.items()]

def set_expected_ph_values(probes):
    def set_expected_ph_values_logic(stdscr, named_ports):
        ph_values = [""]*len(named_ports)
        probe_names = [probe.name if probe.name != None else f"probe{i}" for i, probe in enumerate(probes)]
        pos = 0 # position of the selector

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Enter pH values for the probes:", curses.A_BOLD)
            stdscr.addstr(1, 0, "Navigate with arrow keys, type to enter value, backspace to delete, and press enter when done.")
            for i, (name, ph_value) in enumerate(zip(probe_names, ph_values)):
                if i == pos:
                    stdscr.addstr(i+3, 0, "> " + name + " | pH: " + ph_value + " <")
                else:
                    stdscr.addstr(i+3, 0, "  " + name + " | pH: " + ph_value + "  ")
            stdscr.refresh()

            key = stdscr.getch()

            if key == curses.KEY_UP and pos > 0:
                pos -= 1
            elif key == curses.KEY_DOWN and pos < len(named_ports)-1:
                pos += 1
            elif key == curses.KEY_BACKSPACE:
                ph_values[pos] = ph_values[pos][:-1]
            elif key == ord('\n'): # enter key
                break
            else:
                ph_values[pos] += chr(key)

        ph_values = [float(ph) for ph in ph_values]
        return dict(zip(probe_names, ph_values))
    return curses.wrapper(set_expected_ph_values_logic, probes)

def save_config(named_ports, expected_ph_values=None, file="config.txt"):
    with open(file , "w") as f:
        for port, name in named_ports.items():
            f.write(f"{port} {name}\n")
        if expected_ph_values != None:
            for name, ph in expected_ph_values:
                f.write(f"{name} {ph}\n")

def load_config(file="config.txt"):
    """
    Load the configuration from a file
    paths and names are stored as e.g /dev/sensor1 probe2
    expected ph values are stored in order as plain numbers
    """
    named_ports = {}
    expected_ph_values = []
    with open(file, "r") as f:
        for line in f:
            split_line = line.split()
            if len(split_line) == 2:
                named_ports[split_line[0]] = split_line[1]
            elif len(split_line) == 1:
                expected_ph_values.append(float(split_line[0]))

    if expected_ph_values == []:
        return named_ports, None
    elif len(named_ports) != len(expected_ph_values):
        raise ValueError("The number of expected ph values does not match the number of probes")
    else:
        return named_ports, expected_ph_values
