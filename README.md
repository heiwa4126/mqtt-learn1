# mqtt-learn1

[paho\-mqtt](https://pypi.org/project/paho-mqtt/) v2
の練習

- uv + Python 3.12 + Poe The Poet
- Docker compose で Eclipse Mosquitto

## 開始方法

```sh
uv sync
```

## テスト1

[paho\-mqtt · PyPI](https://pypi.org/project/paho-mqtt/) の
"Getting Started" にある
Subscriber example / publisher example をほぼそのまま

Eclipse Mosquitto をアノニマス接続で、生の MQTT

```sh
poe mqtt
poe logs
# 別のshellで
poe sub1
# 別のshellで
poe pub1
# サーバ止める
poe down
```

2 個メッセージを受けたら、sub1 は終了する。

また fan-out の実験として

```sh
poe sub1
# 別のshellで
poe sub1
# 別のshellで
poe pub1
```

もやってみて。

## Broker Status を mqtt-client 取得するサンプル

事前に
`sudo apt install mosquitto-clients`
が必要

```sh
poe mqtt
poe uptime  # ctrl+cで終了。デフォルトでは10秒ごとにpublishしてる
#
poe clients # 変化がないとpublishしてこない
```

Eclipse Mosquitto の場合
<https://mosquitto.org/man/mosquitto-8.html>
の "Broker Status" の章を参照
