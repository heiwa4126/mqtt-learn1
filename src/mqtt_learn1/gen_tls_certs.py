from __future__ import annotations

import argparse
import os
from pathlib import Path

import trustme

_DEFAULT_SANS = ["*.nip.io", "*.sslip.io", "localhost", "127.0.0.1", "::1"]

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
    parser.add_argument(
        "--san",
        metavar="NAME",
        action="append",
        help="Extra SAN (DNS name or IP) to add to the server cert. Can be repeated.",
    )
    args = parser.parse_args()

    # Collect SANs: defaults + BROKER_HOST env + --san args
    sans: list[str] = list(_DEFAULT_SANS)
    broker_host = os.getenv("BROKER_HOST")
    if broker_host and broker_host not in sans:
        sans.append(broker_host)
    for extra in args.san or []:
        if extra not in sans:
            sans.append(extra)

    ca = trustme.CA()

    server_cert = ca.issue_cert(*sans)

    ca_cert_path = TLS_ROOT / "ca" / "ca.crt"
    server_cert_path = TLS_ROOT / "server" / "server.crt"
    server_key_path = TLS_ROOT / "server" / "server.key"

    write_pem(ca.cert_pem, ca_cert_path, args.force)
    write_pem(server_cert.cert_chain_pems[0], server_cert_path, args.force)
    write_pem(server_cert.private_key_pem, server_key_path, args.force)

    print(f"Server SANs   : {', '.join(sans)}")
    print("Generated TLS materials:")
    print(f"- CA cert      : {ca_cert_path.relative_to(ROOT)}")
    print(f"- Server cert  : {server_cert_path.relative_to(ROOT)}")
    print(f"- Server key   : {server_key_path.relative_to(ROOT)}")

    for device_number in range(1, 6):
        client_id = f"device{device_number}"
        client_cert = ca.issue_cert(
            client_id, common_name=client_id
        )  # CNに追加するだけでSANにも入る
        client_cert_path = TLS_ROOT / "client" / f"{client_id}.crt"
        client_key_path = TLS_ROOT / "client" / f"{client_id}.key"

        write_pem(client_cert.cert_chain_pems[0], client_cert_path, args.force)
        write_pem(client_cert.private_key_pem, client_key_path, args.force)

        print(f"- Client cert  : {client_cert_path.relative_to(ROOT)}")
        print(f"- Client key   : {client_key_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
