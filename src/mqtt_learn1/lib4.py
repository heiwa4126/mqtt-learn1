import os

BROKER = os.getenv("BROKER_HOST", "127.0.0.1")
PORT = 8884
TOPIC = "heiwa4126/mqtt-learn1/test4"
EXPECTED_MESSAGES = 2
