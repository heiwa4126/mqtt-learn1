from paho.mqtt.client import Client, ConnectFlags, MQTTMessage
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode


def make_on_message(topic: str, expected_messages: int):
    def on_message(client: Client, userdata: list[bytes], message: MQTTMessage) -> None:
        # userdata is the structure we choose to provide, here it's a list()
        userdata.append(message.payload)
        print(
            f"received: topic={message.topic}, payload={message.payload.decode(errors='replace')}"
        )
        if len(userdata) >= expected_messages:
            client.unsubscribe(topic)

    return on_message


def make_on_connect(topic: str, qos: int = 1):
    def on_connect(
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
            # we should always subscribe from on_connect callback to be sure
            # our subscribed is persisted across re-connections.
            client.subscribe(topic, qos=qos)

    return on_connect


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


def on_publish(
    client: Client,
    userdata: set[int],
    mid: int,
    reason_code: ReasonCode,
    properties: Properties,
) -> None:
    # reason_code and properties will only be present in MQTTv5. It's always unset in MQTTv3
    try:
        userdata.remove(mid)
    except KeyError:
        print(
            """on_publish() is called with a mid not present in unacked_publish
This is due to an unavoidable race-condition:
* publish() return the mid of the message sent.
* mid from publish() is added to unacked_publish by the main thread
* on_publish() is called by the loop_start thread
While unlikely (because on_publish() will be called after a network round-trip),
 this is a race-condition that COULD happen

The best solution to avoid race-condition is using the msg_info from publish()
We could also try using a list of acknowledged mid rather than removing from pending list,
but remember that mid could be re-used !"""
        )
