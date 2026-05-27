import os
from pathlib import Path

BROKER = os.getenv("BROKER_HOST", "127.0.0.1")
PORT = 8884
TOPIC = "heiwa4126/mqtt-learn1/test5"
EXPECTED_MESSAGES = 2

# TLS certificate paths (relative to project root)
TLS_ROOT = Path(__file__).resolve().parents[2] / "var" / "tls"
CA_CERT = TLS_ROOT / "ca" / "ca.crt"
# for sub5
CLIENT_CERT1 = TLS_ROOT / "client" / "device1.crt"
CLIENT_KEY1 = TLS_ROOT / "client" / "device1.key"
# for pub5
CLIENT_CERT2 = TLS_ROOT / "client" / "device2.crt"
CLIENT_KEY2 = TLS_ROOT / "client" / "device2.key"
