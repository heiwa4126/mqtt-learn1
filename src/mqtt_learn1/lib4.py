import os

BROKER = os.getenv("BROKER_HOST", "127.0.0.1")
PORT = 8884
TOPIC = "heiwa4126/mqtt-learn1/test4"
EXPECTED_MESSAGES = 2

# Username and password authentication from environment variables
MQTT_USERNAME = os.getenv("USER_PUB4", "user_pub4")
MQTT_PASSWORD = os.getenv("PASS_PUB4", "pass_pub4")
