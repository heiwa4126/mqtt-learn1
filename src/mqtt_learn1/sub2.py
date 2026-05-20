import argparse
import json
import threading
import uuid

import paho.mqtt.client as mqtt
from paho.mqtt.client import Client, ConnectFlags, MQTTMessage
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode

from mqtt_learn1.lib2 import BROKER
from mqtt_learn1.sub_lib import on_subscribe as _on_subscribe
from mqtt_learn1.sub_lib import on_unsubscribe as _on_unsubscribe


class MqttClockClient:
    """MQTT Timezone Clock Client"""

    def __init__(self, device_id: str = "device1"):
        self.device_id = device_id
        self.topic_telemetry = f"clock/{self.device_id}/telemetry"
        self.topic_cmd = f"clock/{self.device_id}/cmd"
        self.topic_cmd_resp = f"clock/{self.device_id}/cmd/resp"
        self.topic_status = f"clock/{self.device_id}/status"

        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message
        self.mqttc.on_subscribe = self.on_subscribe
        self.mqttc.on_unsubscribe = self.on_unsubscribe

        self.mqttc.user_data_set([])
        self.messages = []

    def on_subscribe(
        self,
        client: Client,
        userdata: list[bytes],
        mid: int,
        reason_code_list: list[ReasonCode],
        properties: Properties | None,
    ) -> None:
        _on_subscribe(client, userdata, mid, reason_code_list, properties)

    def on_unsubscribe(
        self,
        client: Client,
        userdata: list[bytes],
        mid: int,
        reason_code_list: list[ReasonCode],
        properties: Properties | None,
    ) -> None:
        _on_unsubscribe(client, userdata, mid, reason_code_list, properties)

    def on_message(
        self, client: Client, userdata: list[bytes], message: MQTTMessage
    ) -> None:
        userdata.append(message.payload)
        print(
            f"received: topic={message.topic}, payload={message.payload.decode(errors='replace')}"
        )

    def on_connect(
        self,
        client: Client,
        userdata: list[bytes],
        flags: ConnectFlags,
        reason_code: ReasonCode,
        properties: Properties | None,
    ) -> None:
        if reason_code.is_failure:
            print(
                f"Failed to connect: {reason_code}. loop_forever() will retry connection"
            )
        else:
            client.subscribe(self.topic_telemetry, qos=1)
            client.subscribe(self.topic_cmd_resp, qos=1)

    def input_handler(self) -> None:
        """キー入力を監視するスレッド"""
        print("Commands: 'q' (quit), 't' (Asia/Tokyo), 'u' (UTC), 's' (get status)")
        while True:
            try:
                key = input()
                if key.lower() == "q":
                    print("Unsubscribing...")
                    self.mqttc.unsubscribe([self.topic_telemetry, self.topic_cmd_resp])
                elif key.lower() == "t":
                    # Asia/Tokyo に設定
                    payload = json.dumps(
                        {"req_id": str(uuid.uuid4()), "tz": "Asia/Tokyo"}
                    )
                    self.mqttc.publish(self.topic_cmd, payload, qos=1)
                    print(f"Published to {self.topic_cmd}: {payload}")
                elif key.lower() == "u":
                    # UTC に設定
                    payload = json.dumps({"req_id": str(uuid.uuid4()), "tz": "UTC"})
                    self.mqttc.publish(self.topic_cmd, payload, qos=1)
                    print(f"Published to {self.topic_cmd}: {payload}")
                elif key.lower() == "s":
                    # STATUS を取得 (retain されたメッセージを受け取る)
                    self.mqttc.subscribe(self.topic_status, qos=1)
                    print(
                        f"Subscribed to {self.topic_status} (retained message will be received)"
                    )
            except EOFError:
                break
            except Exception as e:
                print(f"Input handler error: {e}")
                break

    def run(self) -> None:
        """クライアントを実行"""
        self.mqttc.connect(BROKER)

        # キー入力ハンドラーをデーモンスレッドで開始
        thread = threading.Thread(target=self.input_handler, daemon=True)
        thread.start()

        try:
            self.mqttc.loop_forever()
        except KeyboardInterrupt:
            print("\nInterrupted by user, stopping...", flush=True)
            self.mqttc.unsubscribe([self.topic_telemetry, self.topic_cmd_resp])
            print("Waiting for unsubscribe to complete...", flush=True)
            self.mqttc.loop_stop()


def main(device_id: str = "device1") -> None:
    client = MqttClockClient(device_id)
    client.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MQTT Timezone Clock Client")
    parser.add_argument(
        "-i",
        "--id",
        required=False,
        default="device1",
        help="Device ID for this clock client (default: device1)",
    )
    args = parser.parse_args()
    print(f"Starting MQTT Clock Client with device ID: {args.id}")
    main(args.id)
