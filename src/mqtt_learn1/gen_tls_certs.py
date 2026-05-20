from __future__ import annotations

import argparse
from pathlib import Path

import trustme

ROOT = Path(__file__).resolve().parents[2]
TLS_ROOT = ROOT / "var" / "tls"


def write_pem(blob: trustme.Blob, path: Path, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(
            f"{path} already exists. Re-run with --force to overwrite."
        )
    blob.write_to_path(path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate local TLS certs for MQTT broker/client under ./var/tls"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    args = parser.parse_args()

    ca = trustme.CA()

    server_cert = ca.issue_cert(
        "localhost",
        "mqtt",
        "127.0.0.1",
    )
    client_cert = ca.issue_cert("device1")

    ca_cert_path = TLS_ROOT / "ca" / "ca.crt"
    server_cert_path = TLS_ROOT / "server" / "server.crt"
    server_key_path = TLS_ROOT / "server" / "server.key"
    client_cert_path = TLS_ROOT / "client" / "device1.crt"
    client_key_path = TLS_ROOT / "client" / "device1.key"

    write_pem(ca.cert_pem, ca_cert_path, args.force)
    write_pem(server_cert.cert_chain_pems[0], server_cert_path, args.force)
    write_pem(server_cert.private_key_pem, server_key_path, args.force)
    write_pem(client_cert.cert_chain_pems[0], client_cert_path, args.force)
    write_pem(client_cert.private_key_pem, client_key_path, args.force)

    print("Generated TLS materials:")
    print(f"- CA cert      : {ca_cert_path.relative_to(ROOT)}")
    print(f"- Server cert  : {server_cert_path.relative_to(ROOT)}")
    print(f"- Server key   : {server_key_path.relative_to(ROOT)}")
    print(f"- Client cert  : {client_cert_path.relative_to(ROOT)}")
    print(f"- Client key   : {client_key_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
