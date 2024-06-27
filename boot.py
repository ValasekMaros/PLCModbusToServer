import time
import struct
import machine
import network
import auth
from ota import OTAUpdater
from umqttsimple import MQTTClient

machine.freq(80000000)

sta_if = network.WLAN(network.STA_IF)
try:
    sta_if.active(True)
    sta_if.ifconfig((auth.device_IP, auth.mask, auth.gateway, auth.gateway))
    print('Wifi activated')
    sta_if.connect(auth.SSID_Name, auth.SSID_Pass)
except:
    pass
nextcalc = round(time.time_ns() / 1000000) + calc_interval
while not sta_if.isconnected():
    timer = round(time.time_ns() / 1000000)
    if timer >= nextcalc:
        print('Cant connect to WiFi, error')
        endTime = time.time()
        cycleTime = endTime - startBootTime1
        print('Cycle time:', cycleTime)
        print('Error sleep')
        machine.deepsleep((errorTime - cycleTime) * 1000)
        machine.reset()

print('Connection successful')
print(sta_if.ifconfig())

#firmware_url = "https://raw.githubusercontent.com/ValasekMaros/PLCModbusToServer/main/umodbus/"

#ota_updater = OTAUpdater(firmware_url, "boot.py")

#ota_updater.download_and_install_update_if_available()

# import modbus host classes
from umodbus.serial import Serial as ModbusRTUMaster
from umodbus.functions import int_to_bin

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
slave_addr = 1            # address on bus of the client/slave

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
baudrate = 9600
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
     data_bits=8,          # optional, default 8
     stop_bits=1,          # optional, default 1
     parity=None,          # optional, default None
     ctrl_pin=27,          # optional, control DE/RE
    uart_id=uart_id         # optional, default 1, see port specific docs
)

if IS_DOCKER_MICROPYTHON:
    # works only with fake machine UART
    assert host._uart._is_server is False

# commond slave register setup, to be used with the Master example above
register_definitions = {
    "HREGS": {
        "VZDUCH": {
            "register": 0,
            "len": 2,
            "val": 0
        },
        "EXAMPLE_HREG": {
            "register": 0,
            "len": 2,
            "val": 0
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

# READ HREGS
vzduch_hreg_address = register_definitions['HREGS']['VZDUCH']['register']
vzduch_register_qty = register_definitions['HREGS']['VZDUCH']['len']
vzduch_register_value = host.read_holding_registers(
    slave_addr=slave_addr,
    starting_addr=vzduch_hreg_address,
    register_qty=vzduch_register_qty,
    signed=False)
print('Status of HREG {}: {}'.format(vzduch_hreg_address, vzduch_register_value))
register_value = bytearray(vzduch_register_value)
print(vzduch_register_value)
time.sleep(1)
print()

if IS_DOCKER_MICROPYTHON:
    sys.exit(0)
