import os

import paho.mqtt.client as mqtt
from paho.mqtt.client import Client, ConnectFlags, MQTTMessage
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode

from mqtt_learn1.lib4 import (
    BROKER,
    EXPECTED_MESSAGES,
    PORT,
    TOPIC,
)
from mqtt_learn1.sub_lib import on_subscribe, on_unsubscribe

# 環境変数が未定義なら死ぬように, os.getenv() ではなく os.environ[] を使う
MQTT_USERNAME = os.environ["SUB4_USER"]
MQTT_PASSWORD = os.environ["SUB4_PASS"]


def on_message(client: Client, userdata: list[bytes], message: MQTTMessage) -> None:
    # userdata is the structure we choose to provide, here it's a list()
    userdata.append(message.payload)
    print(
        f"received: topic={message.topic}, payload={message.payload.decode(errors='replace')}"
    )
    # Stop after receiving messages published by pub4.py
    if len(userdata) >= EXPECTED_MESSAGES:
        # client.unsubscribe(SYSTEM_TOPIC)
        client.unsubscribe(TOPIC)


def on_connect(
    client: Client,
    userdata: list[bytes],
    flags: ConnectFlags,
    reason_code: ReasonCode,
    properties: Properties | None,
) -> None:
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across re-connections.
        # client.subscribe(SYSTEM_TOPIC)
        client.subscribe(TOPIC, qos=1)


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe
mqttc.on_unsubscribe = on_unsubscribe

# Setup username and password authentication
mqttc.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

mqttc.user_data_set([])
print(f"Connecting to broker {BROKER}:{PORT} with username/password auth...")
mqttc.connect(BROKER, PORT)
mqttc.loop_forever()
print(f"Received the following message: {mqttc.user_data_get()}")
