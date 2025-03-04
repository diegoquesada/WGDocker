#
# mqtt-to-prom.py
# v0.2
# Python script to subscribe to a MQTT topic and make the received data available to Prometheus.
# The script uses the Paho MQTT client and the Prometheus Python client.
# (c) 2025 Diego Quesada
# 

import paho.mqtt.client as mqtt
import json
import time
import os
from prometheus_client import start_http_server, Gauge

# Define the Prometheus metrics we will send
temperature_gauge = Gauge('wio_temperature', 'Temperature received from WioLink', ['serial'])
humidity_gauge = Gauge('wio_humidity', 'Humidity received from WioLink', ['serial'])
lux_gauge = Gauge('wio_lux', 'Light level received from WioLink', ['serial'])
relay_gauge = Gauge('wio_relay', 'Relay state received from WioLink', ['serial'])

# MQTT settings
MQTT_BROKER = "mqtt5"
MQTT_TOPIC = "wioLink/+/sensors"
MQTT_PORT = 1883
MQTT_USER = os.environ['PY_MQTT_USER']
MQTT_PWD = os.environ['PY_MQTT_PWD']

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("mqtt-exporter: Connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"mqtt-exporter: Failed to connect, error {reason_code}")

def on_disconnect(client, userdata, reason_code):
    print("mqtt-exporter: Disconnected from MQTT broker, attempting to reconnect.")
    for attempt in range(1,11): # Retry up to 10 times
        try:
            time.sleep(5)
            client.reconnect()
            print("mqtt-exporter: Reconnected to MQTT broker.")
            return
        except Exception as e:
            print(f"mqtt-exporter: Reconnection failed, {e}.")
    print("mqtt-exporter: Failed to reconnect after 10 attempts.")
    exit(1)

# Callback when a message is received on the subscribed topic
def on_message(client, userdata, message):
    topicArray = message.topic.split('/')
    serialNo = topicArray[1]
    topicCategory = topicArray[2]
    payload = json.loads(message.payload.decode('utf-8'))
    try:
        if topicCategory == 'sensors':
            temperature = payload.get('temperature')
            humidity = payload.get('humidity')
            lux = payload.get('lux')

            print(f'mqtt-exporter: serial: {serialNo}, temperature: {temperature}, humidity: {humidity}, lux: {lux}')

            if temperature is not None:
                temperature_gauge.labels(serial=serialNo).set(temperature)
            if humidity is not None:
                humidity_gauge.labels(serial=serialNo).set(humidity)
            if lux is not None:
                lux_gauge.labels(serial=serialNo).set(lux)
        elif topicCategory == 'relays':
            relay1 = payload.get('relay1')
            relay2 = payload.get('relay2')
            print(f'app.py: serial: {serialNo}, relay1: {relay1}, relay2: {relay2}')
            if relay1 is not None:
                relay_gauge.labels(serial=serialNo).set(relay1)
    except json.JSONDecodeError:
        print("Invalid JSON received")

print("MQTT to Prometheus bridge v0.2")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.username_pw_set(MQTT_USER, MQTT_PWD)
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start() # Non-blocking loop

start_http_server(8080, addr='0.0.0.0') # Listen on all interfaces inside the container

while True:
    time.sleep(1)

