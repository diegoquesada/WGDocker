#
# mqtt-to-prom.py
# Python script to subscribe to a MQTT topic and make the received data available to Prometheus.
# The script uses the Paho MQTT client and the Prometheus Python client.
# 

import paho.mqtt.client as mqtt
import json
import os
from prometheus_client import start_http_server, Gauge

# Define the Prometheus metrics we will send
temperature_gauge = Gauge('wio_temperature', 'Temperature received from WioLink', ['serial'])
humidity_gauge = Gauge('wio_humidity', 'Humidity received from WioLink', ['serial'])
lux_gauge = Gauge('wio_lux', 'Light level received from WioLink', ['serial'])

# MQTT settings
MQTT_BROKER = "mqtt5"
MQTT_TOPIC = "wioLink/+/sensors"
MQTT_PORT = 1883
MQTT_USER = os.environ['PY_MQTT_USER']
MQTT_PWD = os.environ['PY_MQTT_PWD']

# Callback when a message is received on the subscribed topic
def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode('utf-8'))
        temperature = payload.get('temperature')
        humidity = payload.get('humidity')
        lux = payload.get('lux')
        serialNo = message.topic.split('/')[1]

        print(f'app.py: serial: {serialNo}, temperature: {temperature}, humidity: {humidity}, lux: {lux}')

        if temperature is not None:
            temperature_gauge.labels(serial=serialNo).set(temperature)
        if humidity is not None:
            humidity_gauge.labels(serial=serialNo).set(humidity)
        if lux is not None:
            lux_gauge.labels(serial=serialNo).set(lux)
    except json.JSONDecodeError:
        print("Invalid JSON received")

print("MQTT to Prometheus bridge v0.1")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.username_pw_set(MQTT_USER, MQTT_PWD)
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC)

start_http_server(8080, addr='0.0.0.0') # Listen on all interfaces inside the container

client.loop_forever()

