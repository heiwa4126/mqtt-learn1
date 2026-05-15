import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("test.mosquitto.org", 1883)


def on_message(client, userdata, message):
    print("Received message:", str(message.payload.decode("utf-8")))
