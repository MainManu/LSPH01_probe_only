#!/bin/bash

# This script is used to setup the virtual environment for the project.

#check if virtualenv is installed
if ! command -v virtualenv &> /dev/null
then
    echo "virtualenv could not be found. Please install it using 'sudo apt install python3-virtualenv'"
    exit
fi


# check if venv folder exists
if [ -d ".venv" ]
then
    echo "Virtual environment already exists. Skipping creation."
    exit
fi

# Create the virtual environment
virtualenv .venv
source .venv/bin/activate
# let the user select wether to install minimal or raspberry pi requirements
echo "Do you want to install the minimal requirements or the raspberry pi requirements?"
echo "1. Minimal requirements"
echo "2. Raspberry Pi requirements"
read -p "Enter your choice: " choice
if [ $choice -eq 1 ]
then
    pip3 install -r setup/requirements_minimal.txt
elif [ $choice -eq 2 ]
then
    pip3 install -r setup/requirements_rpi.txt
else
    echo "Invalid choice. Exiting."
    exit
fi