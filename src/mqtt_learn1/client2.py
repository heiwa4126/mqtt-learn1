import argparse
import json
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

import paho.mqtt.client as mqtt
from paho.mqtt.client import Client, ConnectFlags, MQTTMessage
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode

from mqtt_learn1.lib2 import BROKER


class TimezoneClock:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.tz = "UTC"  # default timezone
        self.running = True
        self.lock = threading.Lock()

        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message
        self.mqttc.on_disconnect = self.on_disconnect

        self.mqttc.user_data_set(self)

    def get_topic(self, suffix: str) -> str:
        """トピック名を生成する。

        Args:
            suffix: トピック末尾（例: 'telemetry', 'cmd', 'cmd/resp', 'status'）

        Returns:
            フルトピック名（例: 'clock/<ID>/telemetry'）
        """
        return f"clock/{self.device_id}/{suffix}"

    def publish_status(self) -> None:
        """現在のタイムゾーンをステータストピックに配信（retain=true）。

        起動時とタイムゾーン更新時に呼び出される。
        """
        topic = self.get_topic("status")
        payload = json.dumps({"tz": self.tz})
        self.mqttc.publish(topic, payload, qos=1, retain=True)
        print(f"[STATUS] {topic}: {payload}")

    def publish_telemetry(self) -> None:
        """現在時刻を ISO 8601 形式で配信（5秒間隔）。

        現在のタイムゾーン設定に基づいて時刻を生成し、
        テレメトリートピックに配信する。
        """
        topic = self.get_topic("telemetry")
        try:
            tz_info = ZoneInfo(self.tz)
            now = datetime.now(tz=tz_info)
            payload = json.dumps({"time": now.isoformat()})
            self.mqttc.publish(topic, payload, qos=1, retain=False)
            print(f"[TELEMETRY] {topic}: {payload}")
        except Exception as e:
            print(f"[ERROR] Failed to publish telemetry: {e}")

    def publish_response(
        self, req_id: str, status: str, message: str | None = None
    ) -> None:
        """コマンドレスポンスを配信。

        Args:
            req_id: リクエスト識別子（UUID）。コマンドのreq_idをエコーバック。
            status: 'OK' または 'ERROR'。
            message: エラー時のみ、エラー内容の説明文字列。
        """
        topic = self.get_topic("cmd/resp")
        payload_dict = {"req_id": req_id, "status": status}
        if message is not None:
            payload_dict["message"] = message
        payload = json.dumps(payload_dict)
        self.mqttc.publish(topic, payload, qos=1, retain=False)
        print(f"[RESP] {topic}: {payload}")

    def handle_command(self, payload: bytes) -> None:
        """タイムゾーン変更コマンドを処理。

        JSON 形式のコマンドを解析し、タイムゾーン値を検証。
        有効な場合は TZ を更新してステータスを配信、無効な場合はエラーレスポンスを配信。

        Args:
            payload: JSON形式のコマンドペイロード（バイト列）
        """
        try:
            data = json.loads(payload.decode())
            req_id = data.get("req_id")
            tz = data.get("tz")

            if not req_id or not tz:
                print("[CMD] Invalid command: missing req_id or tz")
                return

            # Validate timezone
            if tz not in available_timezones():
                print(f"[CMD] Unknown timezone: {tz}")
                self.publish_response(req_id, "ERROR", f"Unknown timezone: {tz}")
                return

            # Update timezone and publish status
            with self.lock:
                self.tz = tz
            self.publish_status()
            self.publish_response(req_id, "OK")
            print(f"[CMD] Timezone updated to: {tz}")

        except json.JSONDecodeError as e:
            print(f"[CMD] Failed to decode JSON: {e}")
        except Exception as e:
            print(f"[CMD] Unexpected error: {e}")

    def on_connect(
        self,
        client: Client,
        userdata: "TimezoneClock",
        flags: ConnectFlags,
        reason_code: ReasonCode,
        properties: Properties | None,
    ) -> None:
        """Broker 接続時のコールバック。

        接続成功時に初期ステータスを配信し、コマンドトピックをサブスクライブする。
        """
        if reason_code.is_failure:
            print(f"[CONNECT] Failed to connect: {reason_code}")
        else:
            print("[CONNECT] Connected successfully")
            # Publish initial status
            self.publish_status()
            # Subscribe to command topic
            cmd_topic = self.get_topic("cmd")
            client.subscribe(cmd_topic, qos=1)
            print(f"[SUBSCRIBE] Subscribed to {cmd_topic}")

    def on_message(
        self,
        client: Client,
        userdata: "TimezoneClock",
        message: MQTTMessage,
    ) -> None:
        """メッセージ受信時のコールバック。

        コマンドトピックからのメッセージを受け取り、処理を開始する。
        """
        print(f"[MESSAGE] topic={message.topic}, qos={message.qos}")
        if message.topic == self.get_topic("cmd"):
            self.handle_command(message.payload)

    def on_disconnect(
        self,
        client: Client,
        userdata: "TimezoneClock",
        reason_code: ReasonCode | int | None,
        properties: Properties | None,
    ) -> None:
        """Broker 切断時のコールバック。

        切断理由をログ出力する。
        """
        print(f"[DISCONNECT] Disconnected: {reason_code}")

    def telemetry_loop(self) -> None:
        """5秒ごとにテレメトリーを配信するループ。

        別スレッドで実行される。running フラグが False になるまで動作。
        """
        while self.running:
            time.sleep(5)
            self.publish_telemetry()

    def connect(self) -> None:
        """Broker に接続して各種ループを開始。

        MQTT クライアントループとテレメトリー配信スレッドを起動する。
        """
        self.mqttc.connect(BROKER)
        self.mqttc.loop_start()
        print(f"[INIT] Connected to {BROKER}")

        # Start telemetry loop in a separate thread
        telemetry_thread = threading.Thread(target=self.telemetry_loop, daemon=True)
        telemetry_thread.start()

    def disconnect(self) -> None:
        """Broker から切断してクリーンアップ。

        実行フラグを停止し、MQTT クライアントループを停止する。
        """
        self.running = False
        self.mqttc.disconnect()
        self.mqttc.loop_stop()
        print("[SHUTDOWN] Disconnected")


def main() -> None:
    """メインエントリーポイント。

    コマンドライン引数を解析し、TimezoneClock クライアントを起動。
    Ctrl+C で安全にシャットダウン可能。
    """
    parser = argparse.ArgumentParser(description="MQTT Timezone Clock Client")
    parser.add_argument(
        "-i",
        "--id",
        required=True,
        help="Device ID for this clock client",
    )
    args = parser.parse_args()

    client = TimezoneClock(args.id)
    client.connect()

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MAIN] Shutting down...", flush=True)
        client.disconnect()


if __name__ == "__main__":
    main()
