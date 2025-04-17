import time
import threading
import paho.mqtt.client as mqtt
import json

# ─── CONFIG ──────────────────────────────────────────────────────────────
BROKER       = "10.10.10.55"
PORT         = 1883
USERNAME     = "admin"
PASSWORD     = "strongPassword"
CLIENT_ID    = "windows_dummy_node"

CMD_TOPIC    = "plant/windows01/cmd"
RPM_TOPIC    = "plant/windows01/telemetry/rpm"
TEMP_TOPIC   = "plant/windows01/telemetry/temp"

PUBLISH_INT  = 2
AMBIENT_TEMP = 25.0
# ─────────────────────────────────────────────────────────────────────────

# State variables
target_temp = AMBIENT_TEMP
current_temp = AMBIENT_TEMP
heating = False
stir_rpm = 0

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Connected successfully")
        client.subscribe(CMD_TOPIC)
    else:
        print(f"[MQTT] Connection failed: {rc}")

def on_message(client, userdata, msg):
    global target_temp, heating, stir_rpm
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[CMD] {payload}")

        if "stir" in payload and "rate" in payload["stir"]:
            stir_rpm = int(payload["stir"]["rate"])
            print(f" → Stir rate set to {stir_rpm} RPM")

        if "temp" in payload and "set" in payload["temp"]:
            target_temp = float(payload["temp"]["set"])
            heating = True
            print(f" → Target temp set to {target_temp} °C")

    except Exception as e:
        print(" ! Failed to parse JSON command:", e)

def telemetry_loop():
    global current_temp, heating
    while True:
        if heating:
            if current_temp < target_temp:
                current_temp += 0.5
            else:
                heating = False
        else:
            if current_temp > AMBIENT_TEMP:
                current_temp -= 0.1

        client.publish(RPM_TOPIC, stir_rpm)
        client.publish(TEMP_TOPIC, round(current_temp, 2))
        print(f"[TEL] RPM={stir_rpm}, Temp={current_temp:.2f} °C")
        time.sleep(PUBLISH_INT)

# ─── MQTT Setup ──────────────────────────────────────────────────────────
client = mqtt.Client(client_id=CLIENT_ID)
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, keepalive=60)
client.loop_start()

# ─── Telemetry Thread ────────────────────────────────────────────────────
threading.Thread(target=telemetry_loop, daemon=True).start()

# ─── Keep Alive Loop ─────────────────────────────────────────────────────
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down…")
    client.loop_stop()
    client.disconnect()
