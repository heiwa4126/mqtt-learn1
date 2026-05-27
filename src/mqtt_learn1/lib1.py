import os

BROKER = os.getenv("BROKER_HOST", "127.0.0.1")
PORT = 1883
TOPIC = "heiwa4126/mqtt-learn1/test1"
EXPECTED_MESSAGES = 2

SYSTEM_TOPIC = "$SYS/#"
