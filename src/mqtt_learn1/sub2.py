import json
import threading
import uuid

import paho.mqtt.client as mqtt
from paho.mqtt.client import Client, ConnectFlags, MQTTMessage
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode

from mqtt_learn1.lib2 import BROKER

DEVICE_ID = "device1"
TOPIC_TELEMETRY = f"clock/{DEVICE_ID}/telemetry"
TOPIC_CMD = f"clock/{DEVICE_ID}/cmd"
TOPIC_CMD_RESP = f"clock/{DEVICE_ID}/cmd/resp"
TOPIC_STATUS = f"clock/{DEVICE_ID}/status"


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


def on_unsubscribe(
    client: Client,
    userdata: list[bytes],
    mid: int,
    reason_code_list: list[ReasonCode],
    properties: Properties | None,
) -> None:
    # Be careful, the reason_code_list is only present in MQTTv5.
    # In MQTTv3 it will always be empty
    if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
        print("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
    else:
        print(f"Broker replied with failure: {reason_code_list[0]}")
    client.disconnect()


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
        client.subscribe(TOPIC_TELEMETRY, qos=1)
        client.subscribe(TOPIC_CMD_RESP, qos=1)


def input_handler(client: mqtt.Client) -> None:
    """キー入力を監視するスレッド"""
    print("Commands: 'q' (quit), 't' (Asia/Tokyo), 'u' (UTC), 's' (get status)")
    while True:
        try:
            key = input()
            if key.lower() == "q":
                print("Unsubscribing...")
                client.unsubscribe([TOPIC_TELEMETRY, TOPIC_CMD_RESP])
            elif key.lower() == "t":
                # Asia/Tokyo に設定
                payload = json.dumps({"req_id": str(uuid.uuid4()), "tz": "Asia/Tokyo"})
                client.publish(TOPIC_CMD, payload, qos=1)
                print(f"Published to {TOPIC_CMD}: {payload}")
            elif key.lower() == "u":
                # UTC に設定
                payload = json.dumps({"req_id": str(uuid.uuid4()), "tz": "UTC"})
                client.publish(TOPIC_CMD, payload, qos=1)
                print(f"Published to {TOPIC_CMD}: {payload}")
            elif key.lower() == "s":
                # STATUS を取得 (retain されたメッセージを受け取る)
                client.subscribe(TOPIC_STATUS, qos=1)
                print(
                    f"Subscribed to {TOPIC_STATUS} (retained message will be received)"
                )
        except EOFError:
            break
        except Exception as e:
            print(f"Input handler error: {e}")
            break


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe
mqttc.on_unsubscribe = on_unsubscribe

mqttc.user_data_set([])
mqttc.connect(BROKER)

# キー入力ハンドラーをデーモンスレッドで開始
thread = threading.Thread(target=input_handler, args=(mqttc,), daemon=True)
thread.start()

try:
    mqttc.loop_forever()
except KeyboardInterrupt:
    print("\nInterrupted by user, stopping...", flush=True)
    mqttc.unsubscribe([TOPIC_TELEMETRY, TOPIC_CMD_RESP])
    print("Waiting for unsubscribe to complete...", flush=True)
    mqttc.loop_stop()
