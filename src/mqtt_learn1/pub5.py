import time

import paho.mqtt.client as mqtt

from mqtt_learn1.lib5 import BROKER, CA_CERT, CLIENT_CERT2, CLIENT_KEY2, PORT, TOPIC
from mqtt_learn1.lib_common import setup_tls_client
from mqtt_learn1.sub_lib import on_publish

unacked_publish: set[int] = set()
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_publish = on_publish

# Setup TLS
setup_tls_client(mqttc, CA_CERT, CLIENT_CERT2, CLIENT_KEY2)

mqttc.user_data_set(unacked_publish)
mqttc.connect(BROKER, PORT)
mqttc.loop_start()

# Our application produce some messages
msg_info = mqttc.publish(TOPIC, "my message", qos=1)
unacked_publish.add(msg_info.mid)

msg_info2 = mqttc.publish(TOPIC, "my message2", qos=1)
unacked_publish.add(msg_info2.mid)

# Wait for all message to be published
while len(unacked_publish):
    time.sleep(0.1)

# Due to race-condition described above, the following way to wait for all publish is safer
msg_info.wait_for_publish()
msg_info2.wait_for_publish()

mqttc.disconnect()
mqttc.loop_stop()
