import paho.mqtt.client as mqtt
from paho.mqtt.client import Client, ConnectFlags, MQTTMessage
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode

from mqtt_learn1.lib2 import BROKER, TOPIC


def on_subscribe(
    client: Client,
    userdata: list[bytes],
    mid: int,
    reason_code_list: list[ReasonCode],
    properties: Properties | None,
) -> None:
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        print(f"Broker rejected you subscription: {reason_code_list[0]}")
    else:
        print(f"Broker granted the following QoS: {reason_code_list[0].value}")


def on_message(client: Client, userdata: list[bytes], message: MQTTMessage) -> None:
    # userdata is the structure we choose to provide, here it's a list()
    userdata.append(message.payload)
    print(
        f"received: topic={message.topic}, payload={message.payload.decode(errors='replace')}"
    )
    # Stop after receiving messages published by pub1.py


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

mqttc.user_data_set([])
mqttc.connect(BROKER)
mqttc.loop_forever()
