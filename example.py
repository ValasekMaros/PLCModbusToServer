#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Main script

Do your stuff here, this file is similar to the loop() function on Arduino

Create a Modbus RTU host (master) which requests or sets data on a client
device.

The RTU communication pins can be choosen freely (check MicroPython device/
port specific limitations).
The register definitions of the client as well as its connection settings like
bus address and UART communication speed can be defined by the user.
"""

# system packages
import time

# import modbus host classes
from umodbus.serial import Serial as ModbusRTUMaster

IS_DOCKER_MICROPYTHON = False
try:
    import machine
    machine.reset_cause()
except ImportError:
    raise Exception('Unable to import machine, are all fakes available?')
except AttributeError:
    # machine fake class has no "reset_cause" function
    IS_DOCKER_MICROPYTHON = True
    import sys


# ===============================================
# RTU Slave setup
slave_addr = 10             # address on bus of the client/slave

# RTU Master setup
# act as host, collect Modbus data via RTU from a client device
# ModbusRTU can perform serial requests to a client device to get/set data
# check MicroPython UART documentation
# https://docs.micropython.org/en/latest/library/machine.UART.html
# for Device/Port specific setup
#
# RP2 needs "rtu_pins = (Pin(4), Pin(5))" whereas ESP32 can use any pin
# the following example is for an ESP32
# For further details check the latest MicroPython Modbus RTU documentation
# example https://micropython-modbus.readthedocs.io/en/latest/EXAMPLES.html#rtu
rtu_pins = (25, 26)         # (TX, RX)
baudrate = 115200
uart_id = 1

try:
    from machine import Pin
    import os
    from umodbus import version

    os_info = os.uname()
    print('MicroPython infos: {}'.format(os_info))
    print('Used micropthon-modbus version: {}'.format(version.__version__))

    if 'pyboard' in os_info:
        # NOT YET TESTED !
        # https://docs.micropython.org/en/latest/library/pyb.UART.html#pyb-uart
        # (TX, RX) = (X9, X10) = (PB6, PB7)
        uart_id = 1
        # (TX, RX)
        rtu_pins = (Pin(PB6), Pin(PB7))     # noqa: F821
    elif 'esp8266' in os_info:
        # https://docs.micropython.org/en/latest/esp8266/quickref.html#uart-serial-bus
        raise Exception(
            'UART0 of ESP8266 is used by REPL, UART1 can only be used for TX'
        )
    elif 'esp32' in os_info:
        # https://docs.micropython.org/en/latest/esp32/quickref.html#uart-serial-bus
        uart_id = 1
        rtu_pins = (25, 26)             # (TX, RX)
    elif 'rp2' in os_info:
        # https://docs.micropython.org/en/latest/rp2/quickref.html#uart-serial-bus
        uart_id = 0
        rtu_pins = (Pin(0), Pin(1))     # (TX, RX)
except AttributeError:
    pass
except Exception as e:
    raise e

print('Using pins {} with UART ID {}'.format(rtu_pins, uart_id))

host = ModbusRTUMaster(
    pins=rtu_pins,          # given as tuple (TX, RX)
    baudrate=baudrate,      # optional, default 9600
    # data_bits=8,          # optional, default 8
    # stop_bits=1,          # optional, default 1
    # parity=None,          # optional, default None
     ctrl_pin=27,          # optional, control DE/RE
    uart_id=uart_id         # optional, default 1, see port specific docs
)

if IS_DOCKER_MICROPYTHON:
    # works only with fake machine UART
    assert host._uart._is_server is False

# commond slave register setup, to be used with the Master example above
register_definitions = {
    "COILS": {
        "RESET_REGISTER_DATA_COIL": {
            "register": 42,
            "len": 1,
            "val": 0
        },
        "EXAMPLE_COIL": {
            "register": 123,
            "len": 1,
            "val": 1
        }
    },
    "HREGS": {
        "EXAMPLE_HREG": {
            "register": 93,
            "len": 1,
            "val": 19
        }
    },
    "ISTS": {
        "EXAMPLE_ISTS": {
            "register": 67,
            "len": 1,
            "val": 0
        }
    },
    "IREGS": {
        "EXAMPLE_IREG": {
            "register": 10,
            "len": 1,
            "val": 60001
        }
    }
}

"""
# alternatively the register definitions can also be loaded from a JSON file
import json

with open('registers/example.json', 'r') as file:
    register_definitions = json.load(file)
"""

print('Requesting and updating data on RTU client at address {} with {} baud'.
      format(slave_addr, baudrate))
print()

# READ COILS
coil_address = register_definitions['COILS']['EXAMPLE_COIL']['register']
coil_qty = register_definitions['COILS']['EXAMPLE_COIL']['len']
coil_status = host.read_coils(
    slave_addr=slave_addr,
    starting_addr=coil_address,
    coil_qty=coil_qty)
print('Status of COIL {}: {}'.format(coil_address, coil_status))
time.sleep(1)

# WRITE COILS
new_coil_val = 0
operation_status = host.write_single_coil(
    slave_addr=slave_addr,
    output_address=coil_address,
    output_value=new_coil_val)
print('Result of setting COIL {} to {}'.format(coil_address, operation_status))
time.sleep(1)

# READ COILS again
coil_status = host.read_coils(
    slave_addr=slave_addr,
    starting_addr=coil_address,
    coil_qty=coil_qty)
print('Status of COIL {}: {}'.format(coil_address, coil_status))
time.sleep(1)

print()

# READ HREGS
hreg_address = register_definitions['HREGS']['EXAMPLE_HREG']['register']
register_qty = register_definitions['HREGS']['EXAMPLE_HREG']['len']
register_value = host.read_holding_registers(
    slave_addr=slave_addr,
    starting_addr=hreg_address,
    register_qty=register_qty,
    signed=False)
print('Status of HREG {}: {}'.format(hreg_address, register_value))
time.sleep(1)

# WRITE HREGS
new_hreg_val = 44
operation_status = host.write_single_register(
    slave_addr=slave_addr,
    register_address=hreg_address,
    register_value=new_hreg_val,
    signed=False)
print('Result of setting HREG {} to {}'.format(hreg_address, operation_status))
time.sleep(1)

# READ HREGS again
register_value = host.read_holding_registers(
    slave_addr=slave_addr,
    starting_addr=hreg_address,
    register_qty=register_qty,
    signed=False)
print('Status of HREG {}: {}'.format(hreg_address, register_value))
time.sleep(1)

print()

# READ ISTS
ist_address = register_definitions['ISTS']['EXAMPLE_ISTS']['register']
input_qty = register_definitions['ISTS']['EXAMPLE_ISTS']['len']
input_status = host.read_discrete_inputs(
    slave_addr=slave_addr,
    starting_addr=ist_address,
    input_qty=input_qty)
print('Status of IST {}: {}'.format(ist_address, input_status))
time.sleep(1)

print()

# READ IREGS
ireg_address = register_definitions['IREGS']['EXAMPLE_IREG']['register']
register_qty = register_definitions['IREGS']['EXAMPLE_IREG']['len']
register_value = host.read_input_registers(
    slave_addr=slave_addr,
    starting_addr=ireg_address,
    register_qty=register_qty,
    signed=False)
print('Status of IREG {}: {}'.format(ireg_address, register_value))
time.sleep(1)

print()

# reset all registers back to their default values on the client
# WRITE COILS
print('Resetting register data to default values...')
coil_address = \
    register_definitions['COILS']['RESET_REGISTER_DATA_COIL']['register']
new_coil_val = True
operation_status = host.write_single_coil(
    slave_addr=slave_addr,
    output_address=coil_address,
    output_value=new_coil_val)
print('Result of setting COIL {}: {}'.format(coil_address, operation_status))
time.sleep(1)

print()

print("Finished requesting/setting data on client")

if IS_DOCKER_MICROPYTHON:
    sys.exit(0)