import time
import json
import threading
from paho.mqtt.client import Client

# MQTT Configuration
BROKER = "10.10.10.55"
PORT = 1883
USERNAME = "admin"
PASSWORD = "strongpass"

# Simulated hotplate state
hotplate = {
    "target_temp": 0,
    "current_temp": 20.0,
    "heat_pwm": 0,
    "stir_rpm": 0
}

# Simulated syringe pump state
pump = {
    "running": False,
    "rate": 0,
    "tip": "",
    "duration": 0,
    "start_time": None
}

client = Client(client_id="simulator-agent")
client.username_pw_set(USERNAME, PASSWORD)

def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT broker (code {}):".format(rc))
    client.subscribe("plant/hotplate01/cmd")
    client.subscribe("plant/syringe01/cmd")
 
def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print("❌ Invalid JSON:", msg.payload.decode())
        return

    if msg.topic == "plant/hotplate01/cmd":
        if "heat" in data:
            hotplate["target_temp"] = data["heat"].get("target", hotplate["target_temp"])
        if "stir" in data:
            hotplate["stir_rpm"] = data["stir"].get("rpm", hotplate["stir_rpm"])
        print(f"[🔥 Hotplate] Command received: {data}")

    elif msg.topic == "plant/syringe01/cmd":
        flow = data.get("flow", {})
        pump["rate"] = flow.get("rate", 0)
        pump["tip"] = flow.get("tip", "")
        pump["duration"] = flow.get("duration", 0)
        pump["start_time"] = time.time()
        pump["running"] = True
        print(f"[💧 Pump] Started dispensing: {flow}")

def telemetry_loop():
    while True:
        # 🔥 Simulate heating — faster when PWM is higher
        if hotplate["current_temp"] < hotplate["target_temp"]:
            heat_rate = (hotplate["heat_pwm"] / 255.0) * 2.0  # up to 2.0 °C/cycle
            hotplate["current_temp"] += heat_rate
            hotplate["heat_pwm"] = min(hotplate["heat_pwm"] + 5, 255)
        elif hotplate["current_temp"] > hotplate["target_temp"]:
            hotplate["current_temp"] -= 0.2
            hotplate["heat_pwm"] = max(hotplate["heat_pwm"] - 5, 0)

        # Send hotplate telemetry
        client.publish("plant/hotplate01/telemetry/temp", round(hotplate["current_temp"], 1))
        client.publish("plant/hotplate01/telemetry/heat_pwm", hotplate["heat_pwm"])
        client.publish("plant/hotplate01/telemetry/target_temp", hotplate["target_temp"])

        # 🕒 Handle pump timing
        if pump["running"]:
            elapsed = time.time() - pump["start_time"]
            if elapsed >= pump["duration"]:
                pump["running"] = False
                print("[✅ Pump] Dispensing complete.")

        time.sleep(2)

# Setup MQTT client
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)

# Start background telemetry
threading.Thread(target=telemetry_loop, daemon=True).start()

# Main loop
client.loop_forever()
