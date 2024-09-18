#!/bin/bash

# This script is used to setup the udev rules for the sensors. The sensors are distignuished by their physical USB port, which is mapped to a symlink in /dev.

#check if directProbeAccess is installed
if [ ! -d "directProbeAccess" ]
then
    echo "directProbeAccess is not installed. Trying parent directory..."
    if [ ! -d "../directProbeAccess" ]
    then
        echo "directProbeAccess not found. Exiting."
    exit
    else
        cd ..
    fi
fi

cwd=$(pwd)
python_code="\
import sys;\
sys.path.append('$cwd');\
from directProbeAccess import setup_udev_rules;\
setup_udev_rules(export=True)"

# check if venv folder exists
if [ ! -d ".venv" ]
then
    echo "Virtual environment does not exist. Trying pipenv..."

    # check wether pipenv is installed
    if ! command -v pipenv &> /dev/null
    then
        echo "pipenv could not be found. Please install it using 'sudo apt install pipenv'"
        exit
    fi

    # check if Pipfile exists
    if [ ! -f "Pipfile" ]
    then
        echo "Pipfile not found. Exiting."
        exit
    fi
    #run python code in pipenv
    pipenv run python3 -c "$python_code"
else
    #run the python code in the virtual environment
    source .venv/bin/activate
    python3 -c "$python_code"
fi

#move export_udev_rules.txt to /etc/udev/rules.d/10-local.rules
sudo mv export_udev_rules.txt /etc/udev/rules.d/10-local-phsens.rules
sudo chown root:root /etc/udev/rules.d/10-local-phsens.rules
sudo chmod 644 /etc/udev/rules.d/10-local-phsens.rules

# reload the udev rules
sudo udevadm control --reload-rules && sudo udevadm trigger

