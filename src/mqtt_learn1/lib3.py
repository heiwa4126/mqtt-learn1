import os
from pathlib import Path

BROKER = os.getenv("BROKER_HOST", "127.0.0.1")
PORT = 8883
TOPIC = "heiwa4126/mqtt-learn1/test3"
EXPECTED_MESSAGES = 2

# TLS certificate paths (relative to project root)
TLS_ROOT = Path(__file__).resolve().parents[2] / "var" / "tls"
CA_CERT = TLS_ROOT / "ca" / "ca.crt"
# CLIENT_CERT = TLS_ROOT / "client" / "device1.crt"
# CLIENT_KEY = TLS_ROOT / "client" / "device1.key"
