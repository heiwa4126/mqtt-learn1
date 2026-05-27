import os
from pathlib import Path

BROKER = os.getenv("BROKER_HOST", "127.0.0.1")
PORT = 8884
TOPIC = "heiwa4126/mqtt-learn1/test4"
EXPECTED_MESSAGES = 2

# TLS certificate paths (relative to project root)
TLS_ROOT = Path(__file__).resolve().parents[2] / "var" / "tls"
CA_CERT = TLS_ROOT / "ca" / "ca.crt"
