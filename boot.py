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
calc_interval = 60
runCycle = 60
topic_pub = 'Pool'
mqtt_client = "PoolDevice00"
powerModbus = machine.Pin(16, machine.Pin.OUT)
powerModbus.on()

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
            machine.reset()
    print('Connection successful')
    print(sta_if.ifconfig())
    
def OTA():
    try:
        firmware_url = "https://raw.githubusercontent.com/ValasekMaros/PLCModbusToServer/main/"
        ota_updater = OTAUpdater(firmware_url, "boot.py")
        ota_updater.download_and_install_update_if_available()
    except:
        pass

def hrefDownload():
    try:
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
    except:
        message['vzduch'] = None
        message['voda'] = None
def MQTTSend():
    try:
        mqtt = MQTTClient(mqtt_client, auth.mqtt_host, auth.mqtt_port, auth.mqtt_user, auth.mqtt_pass)
        mqtt.connect()
    except:
        machine.reset()
    else:
        print(message)
        mqtt.publish(topic_pub, json.dumps(message), False, 1)
        
# ===============================================
# RTU Slave setup
slave_addr = 1            # address on bus of the client/slave
rtu_pins = (17, 5)         # (TX, RX)
baudrate = 9600
uart_id = 1

print('Using pins {} with UART ID {}'.format(rtu_pins, uart_id))

host = ModbusRTUMaster(
    pins=rtu_pins,          # given as tuple (TX, RX)
    baudrate=baudrate,      # optional, default 9600
     data_bits=8,          # optional, default 8
     stop_bits=1,          # optional, default 1
     parity=None,          # optional, default None
     ctrl_pin=18,          # optional, control DE/RE
    uart_id=uart_id         # optional, default 1, see port specific docs
)

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
while True:
    try:
        wifiConnect()
        OTA()
        hrefDownload()
        MQTTSend()
        powerModbus.off()
        runEnd = time.time()
        runDuration = runEnd - runStart
        print(runStart)
        print(runEnd)
        print(runDuration)
        if (runDuration < runCycle):
            print('Cycle time:', runDuration)
            sleep = runCycle - runEnd
            print('Sleep time:', sleep)
            machine.deepsleep(sleep * 1000)
        else:
            machine.reset()
    except:
        machine.reset()
# ----------MAIN PROGRAM----------
machine.reset()
