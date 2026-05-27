import paho.mqtt.client as mqtt

from mqtt_learn1.lib3 import (
    BROKER,
    CA_CERT,
    EXPECTED_MESSAGES,
    PORT,
    TOPIC,
)
from mqtt_learn1.lib_common import setup_tls_client
from mqtt_learn1.sub_lib import (
    make_on_connect,
    make_on_message,
    on_subscribe,
    on_unsubscribe,
)

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = make_on_connect(TOPIC)
mqttc.on_message = make_on_message(TOPIC, EXPECTED_MESSAGES)
mqttc.on_subscribe = on_subscribe
mqttc.on_unsubscribe = on_unsubscribe

# Setup TLS
setup_tls_client(mqttc, CA_CERT)

mqttc.user_data_set([])
print(f"Connecting to broker {BROKER}:{PORT} with TLS...")

mqttc.connect(BROKER, PORT)
mqttc.loop_forever()
print(f"Received the following message: {mqttc.user_data_get()}")
