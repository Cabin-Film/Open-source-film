# hotplate_control.py

import os
import glob
import time
import spidev
import paho.mqtt.client as mqtt
import threading

# ─── SPI Digital Pot Setup ───────────────────────────────────────────────
spi = spidev.SpiDev()
spi.max_speed_hz = 1000000

CS_HEAT = 0  # CE0
CS_RPM = 1   # CE1

def set_pot(channel, value):
    assert 0 <= value <= 255
    spi.open(0, channel)
    spi.xfer2([0x00, value])  # 0x00 = write to wiper 0
    spi.close()

# ─── DS18B20 Temperature Sensor ──────────────────────────────────────────
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28-*')[0]  # assumes one sensor
device_file = device_folder + '/w1_slave'

def read_temp_c():
    with open(device_file, 'r') as f:
        lines = f.readlines()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        with open(device_file, 'r') as f:
            lines = f.readlines()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        return float(temp_string) / 1000.0
    return None

# ─── MQTT Setup ──────────────────────────────────────────────────────────
BROKER = "10.10.10.55"
PORT = 1883
USERNAME = "admin"
PASSWORD = "strongpass"
CLIENT_ID = "hotplate_pi_node"

CMD_TOPIC = "plant/hotplate01/cmd"
TEL_TOPIC = "plant/hotplate01/telemetry"

TARGET_TEMP = 60  # °C (default)
FIXED_RPM_VALUE = 120  # 0–255 scale for stirring speed
DEADBAND = 1.5  # °C

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe(CMD_TOPIC)

def on_message(client, userdata, msg):
    global TARGET_TEMP, FIXED_RPM_VALUE
    import json
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[CMD] {payload}")

        if "heat" in payload and "target" in payload["heat"]:
            TARGET_TEMP = float(payload["heat"]["target"])
            print(f" → New target temp: {TARGET_TEMP} °C")

        if "stir" in payload and "rpm" in payload["stir"]:
            FIXED_RPM_VALUE = int(payload["stir"]["rpm"])
            FIXED_RPM_VALUE = min(max(FIXED_RPM_VALUE, 0), 255)
            print(f" → New RPM setpoint: {FIXED_RPM_VALUE}")
            set_pot(CS_RPM, FIXED_RPM_VALUE)

    except Exception as e:
        print("! Failed to process MQTT command:", e)

client = mqtt.Client(client_id=CLIENT_ID)
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, keepalive=60)
client.loop_start()

# ─── Control Loop ────────────────────────────────────────────────────────
def control_loop():
    print("🔥 Starting hot plate control loop...")
    set_pot(CS_RPM, FIXED_RPM_VALUE)

    try:
        while True:
            temp = read_temp_c()
            error = TARGET_TEMP - temp

            # Deadband logic
            if abs(error) <= DEADBAND:
                heat_value = 0
                gain = 0
            else:
                # Adaptive heat gain based on error magnitude
                if abs(error) > 20:
                    gain = 5
                elif abs(error) > 8:
                    gain = 3
                elif abs(error) > 3:
                    gain = 2
                else:
                    gain = 1

                heat_value = min(max(int(error * gain), 0), 255)

            print(f"Temp: {temp:.2f} °C | Heat PWM: {heat_value} | Target: {TARGET_TEMP} °C | Gain: {gain}")

            set_pot(CS_HEAT, heat_value)
            client.publish(TEL_TOPIC + "/temp", round(temp, 2))
            client.publish(TEL_TOPIC + "/heat_pwm", heat_value)
            client.publish(TEL_TOPIC + "/target_temp", TARGET_TEMP)

            time.sleep(2)

    except KeyboardInterrupt:
        print("🛑 Shutting down...")
        set_pot(CS_HEAT, 0)
        set_pot(CS_RPM, 0)

threading.Thread(target=control_loop, daemon=True).start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
