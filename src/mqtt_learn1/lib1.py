import os

BROKER = os.getenv("BROKER_HOST", "127.0.0.1")
TOPIC = "heiwa4126/mqtt-learn1/test1"
SYSTEM_TOPIC = "$SYS/#"
EXPECTED_MESSAGES = 2
