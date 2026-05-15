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

[paho/test/topic](https://pypi.org/project/paho-mqtt/) の Getting Started にある
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
