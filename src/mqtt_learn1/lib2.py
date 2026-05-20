import os

BROKER = os.getenv("BROKER_HOST", "127.0.0.1")
TOPIC = "clock/device1/telemetry"
