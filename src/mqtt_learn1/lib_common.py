from __future__ import annotations

import ssl
from pathlib import Path

import paho.mqtt.client as mqtt


def setup_tls_client(
    client: mqtt.Client,
    ca_certs: str | Path,
    certfile: str | Path,
    keyfile: str | Path,
) -> None:
    """Configure TLS settings for paho-mqtt client.

    Args:
        client: paho.mqtt.Client instance
        ca_certs: Path to CA certificate file
        certfile: Path to client certificate file
        keyfile: Path to client private key file
    """
    client.tls_set(
        ca_certs=str(ca_certs),
        certfile=str(certfile),
        keyfile=str(keyfile),
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLSv1_2,
        ciphers=None,
    )
    client.tls_insecure_set(False)
