import time
import struct
import machine
import network
import auth
from ota import OTAUpdater
from umqttsimple import MQTTClient
from umodbus.serial import Serial as ModbusRTUMaster
from umodbus.functions import int_to_bin
import json

machine.freq(80000000)

try:
    rtc = machine.RTC()
    rtc.datetime([2000,1,1,5,0,0,0,0])
except:
    pass

runStart = time.time()
calc_interval = 30
runCycle = 60
topic_pub = 'Pool'
mqtt_client = "PoolDevice00"

def wifiConnect():
    sta_if = network.WLAN(network.STA_IF)
    try:
        sta_if.active(True)
        sta_if.ifconfig((auth.device_IP, auth.mask, auth.gateway, auth.gateway))
        print('Wifi activated')
        sta_if.connect(auth.SSID_Name, auth.SSID_Pass)
    except:
        pass
    nextcalc = time.time() + calc_interval
    while not sta_if.isconnected():
        timer = time.time()
        if timer >= nextcalc:
            print('Cant connect to WiFi, error')
            endTime = time.time()
            cycleTime = endTime - runStart
            print('Cycle time:', cycleTime)
            print('Error sleep')
            machine.deepsleep((runCycle - cycleTime) * 1000)
            machine.reset()
    print('Connection successful')
    print(sta_if.ifconfig())
    
def OTA():
    firmware_url = "https://raw.githubusercontent.com/ValasekMaros/PLCModbusToServer/main/"
    ota_updater = OTAUpdater(firmware_url, "boot.py")
    ota_updater.download_and_install_update_if_available()
    pass

def hrefDownload():
    print('Requesting and updating data on RTU client at address {} with {} baud'.format(slave_addr, baudrate))
    print()
    hreg_address = register_definitions['HREGS']['DATA']['register']
    register_qty = register_definitions['HREGS']['DATA']['len']
    register_value = host.read_holding_registers(
        slave_addr=slave_addr,
        starting_addr=hreg_address,
        register_qty=register_qty,
        signed=False)
    print('Status of HREG {}: {}'.format(hreg_address, register_value))
    vzduch = register_value[0] / 100
    voda = register_value[1] / 100
    message['vzduch'] = vzduch
    message['voda'] = voda
    print('Vzduch:', vzduch)
    print('Voda:', voda)
    
def MQTTSend():
    try:
        mqtt = MQTTClient(mqtt_client, auth.mqtt_host, auth.mqtt_port, auth.mqtt_user, auth.mqtt_pass)
        mqtt.connect()
        time.sleep(1)
        print(message)
        mqtt.publish(topic_pub, json.dumps(message), False, 1)
    except:
        machine.reset()

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
rtu_pins = (15, 2)         # (TX, RX)
baudrate = 9600
uart_id = 1

print('Using pins {} with UART ID {}'.format(rtu_pins, uart_id))

host = ModbusRTUMaster(
    pins=rtu_pins,          # given as tuple (TX, RX)
    baudrate=baudrate,      # optional, default 9600
     data_bits=8,          # optional, default 8
     stop_bits=1,          # optional, default 1
     parity=None,          # optional, default None
     ctrl_pin=4,          # optional, control DE/RE
    uart_id=uart_id         # optional, default 1, see port specific docs
)

if IS_DOCKER_MICROPYTHON:
    # works only with fake machine UART
    assert host._uart._is_server is False

# commond slave register setup, to be used with the Master example above
register_definitions = {
    "HREGS": {
        "DATA": {
            "register": 0,
            "len": 2,
            "val": 0
        }
    }
}

message = {
    "vzduch": None,
    "voda": None
    }

# ----------MAIN PROGRAM----------
wifiConnect()
OTA()
hrefDownload()
MQTTSend()
runEnd = time.time()
runDuration = runEnd - runStart
print(runStart)
print(runEnd)
print(runDuration)
if (runDuration < runCycle):
    print('Cycle time:', runDuration)
    sleep = runCycle - runDuration
    print('Sleep time:', sleep)
    machine.deepsleep(sleep * 1000)
else:
    machine.reset()
# ----------MAIN PROGRAM----------

if IS_DOCKER_MICROPYTHON:
    sys.exit(0)
