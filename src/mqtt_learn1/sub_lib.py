from paho.mqtt.client import Client
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode


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
