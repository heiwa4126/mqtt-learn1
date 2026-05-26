#!/usr/bin/env bash
# docker内の mosquitto_passwd コマンドを使って、ユーザ名とパスワードの組み合わせを生成する
#


set -euo pipefail

source .env

PASSWORD_DIR="$PWD/docker/tls4/mosquitto/config"
rm -rf "$PASSWORD_DIR/passwd"

docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "$PASSWORD_DIR:/work" \
  eclipse-mosquitto \
  sh -c "\
mosquitto_passwd -c -b /work/passwd $PUB4_USER $PUB4_PASS ;\
mosquitto_passwd -b /work/passwd $SUB4_USER $SUB4_PASS"

chmod 644 "$PASSWORD_DIR/passwd"
