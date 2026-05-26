#!/usr/bin/env python3
"""
Generate mosquitto password file entries using mosquitto_passwd via Docker.

Usage:
    python gen_passwd.py <username> <password> [output_file]

Example:
    python gen_passwd.py user_pub4 pass_pub4  # prints to stdout
    python gen_passwd.py user_pub4 pass_pub4 docker/tls4/mosquitto/config/passwd  # creates/updates file

Uses Docker with proper user/group mapping to avoid permission issues.
Reference: https://mosquitto.org/man/mosquitto_passwd-1.html
"""

import os
import subprocess
import sys
import tempfile


def generate_mosquitto_passwd_entry(
    username: str, password: str, output_file: str | None = None
) -> str:
    """
    Generate mosquitto password entry using docker and mosquitto_passwd.

    Args:
        username: Username for mosquitto
        password: Plain text password
        output_file: Optional file to write to (creates new or appends)

    Returns:
        Password entry string (username:hash)
    """
    try:
        # Get current user/group IDs
        uid = os.getuid()
        gid = os.getgid()
        cwd = os.getcwd()

        if output_file:
            # Determine if file exists (to decide between -c and no flag)
            file_exists = os.path.exists(output_file)
            file_path = os.path.join(cwd, output_file)

            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # If file doesn't exist, use -c to create it
            flags = ["-b"] if file_exists else ["-c", "-b"]

            cmd = [
                "docker",
                "run",
                "--rm",
                "-u",
                f"{uid}:{gid}",
                "-v",
                f"{cwd}:/work",
                "eclipse-mosquitto",
                "sh",
                "-c",
                f"mosquitto_passwd {' '.join(flags)} /work/{output_file} {username} {password}",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                print(
                    f"Error generating password file: {result.stderr}", file=sys.stderr
                )
                sys.exit(1)

            # Read the generated file to return the entry
            with open(file_path, "r") as f:
                lines = f.readlines()
                # Find the line for this username
                for line in lines:
                    if line.startswith(f"{username}:"):
                        return line.strip()

            return ""
        else:
            # Just generate and print (create temp file, read it, delete it)
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".txt", dir=cwd
            ) as tmp:
                tmp_name = os.path.basename(tmp.name)

            try:
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-u",
                    f"{uid}:{gid}",
                    "-v",
                    f"{cwd}:/work",
                    "eclipse-mosquitto",
                    "sh",
                    "-c",
                    f"mosquitto_passwd -c -b /work/{tmp_name} {username} {password}",
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

                if result.returncode != 0:
                    print(
                        f"Error generating password: {result.stderr}", file=sys.stderr
                    )
                    sys.exit(1)

                # Read the temp file
                with open(os.path.join(cwd, tmp_name), "r") as f:
                    return f.read().strip()
            finally:
                # Clean up temp file
                tmp_path = os.path.join(cwd, tmp_name)
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

    except FileNotFoundError:
        print("Error: Docker is not installed or not in PATH", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Error: mosquitto_passwd command timed out", file=sys.stderr)
        sys.exit(1)


def main():
    """Generate password entry or write to file."""
    if len(sys.argv) < 3:
        print("Usage: python gen_passwd.py <username> <password> [output_file]")
        print("Example: python gen_passwd.py user_pub4 pass_pub4")
        print(
            "         python gen_passwd.py user_pub4 pass_pub4 docker/tls4/mosquitto/config/passwd"
        )
        print("\nThis command requires Docker to be installed and running.")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    result = generate_mosquitto_passwd_entry(username, password, output_file)

    if output_file:
        print(f"Password for {username} written to: {output_file}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
