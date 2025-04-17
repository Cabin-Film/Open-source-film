# syringe_pump_mqtt_agent.py

import time
import threading
import csv
import json
import os
import paho.mqtt.client as mqtt
from adafruit_motorkit import MotorKit

# ─── CONFIG ──────────────────────────────────────────────────────────────
BROKER = "10.10.10.55"
PORT = 1883
USERNAME = "admin"
PASSWORD = "strongpass"
CLIENT_ID = "syringe_pi_node"

CMD_TOPIC = "plant/syringe01/cmd"
TEL_TOPIC = "plant/syringe01/telemetry"

TIP_PROFILE_DIR = "tip_profiles"
MAX_REVOLUTIONS = 800
STEPS_PER_REV = 200  # 200 full steps per rev for 1.8° stepper

# ─── Motor Setup ─────────────────────────────────────────────────────────
kit = MotorKit()
stepper_motor = kit.stepper1  # Use stepper1 or stepper2 depending on wiring

# Simulated total revolutions counter
total_revolutions = 0
lock = threading.Lock()

# ─── CSV LOADING ─────────────────────────────────────────────────────────
def load_tip_profile(tip_size):
    csv_path = os.path.join(TIP_PROFILE_DIR, f"{tip_size}.csv")
    profile = {}
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            profile[float(row['ml_per_min'])] = float(row['rpm'])
    return profile

# ─── FLOW EXECUTION ──────────────────────────────────────────────────────
def execute_flow(rpm, duration_sec):
    global total_revolutions
    revs_per_min = rpm / 60
    total_revs = revs_per_min * duration_sec

    with lock:
        if total_revolutions + total_revs > MAX_REVOLUTIONS:
            print("! Flow rejected: exceeds maximum revolutions")
            return
        total_revolutions += total_revs

    print(f"→ Running at {rpm} RPM for {duration_sec} sec ({total_revs:.2f} revs)")

    delay_per_step = 60 / (rpm * STEPS_PER_REV)  # seconds per step
    total_steps = int(total_revs * STEPS_PER_REV)

    try:
        for step in range(total_steps):
            stepper_motor.onestep(direction=1, style=2)  # FORWARD, DOUBLE style
            time.sleep(delay_per_step)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        stepper_motor.release()

    print("→ Flow complete")

# ─── MQTT CALLBACKS ──────────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe(CMD_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[CMD] {payload}")

        if "flow" in payload:
            flow = payload["flow"]
            rate = float(flow["rate"])
            units = flow.get("units", "ml_per_min")
            tip = flow["tip"]
            duration = int(flow["duration"])

            profile = load_tip_profile(tip)
            if rate not in profile:
                print(f"! Rate {rate} ml/min not found in tip profile for {tip}")
                return

            rpm = profile[rate]
            threading.Thread(target=execute_flow, args=(rpm, duration), daemon=True).start()

    except Exception as e:
        print("! Failed to process message:", e)

# ─── MAIN ────────────────────────────────────────────────────────────────
client = mqtt.Client(client_id=CLIENT_ID)
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, keepalive=60)
client.loop_start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down...")
    client.loop_stop()
    client.disconnect()
