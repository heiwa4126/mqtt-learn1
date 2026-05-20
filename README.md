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

## すこし MQTT クライアントっぽい client2

client2 は MQTT で 5 秒ごとに現在時刻を配信し、タイムゾーン変更コマンドに対応する。[client2 設計書](client2-spec.md)

client2 に対するクライアントが sub2 で、起動すると
"Commands: 'q' (quit), 't' (Asia/Tokyo), 'u' (UTC), 's' (get status)"
(q\[RET\]のようにリターンキー必要)のコマンドが使える。

```sh
poe mqtt
poe logs
# 別のshellで
poe client2
# 別のshellで
poe sub2
# サーバ止める
poe down
```

## 注意: tzdata パッケージを消さないこと

tzdata はコード中では参照されていないが、
Windows の場合

```python
from zoneinfo import ZoneInfo
tz_info = ZoneInfo("UTC")
```

が
`No time zone found with key UTC` 例外になる。

## ブローカをTLS対応にして、8883/TCPで待ち受ける

```sh
poe tls_certs  # ./var 以下に CAとサーバ証明書を作る。証明書の上書きはしない。
## ↑ ついでにクライアント証明書も作る
## ↑ 上書きしたい場合は `poe tls_certs_force` で
poe mqtt_tls
poe logs_tls
# 止めるときは `poe down_tls` で
```

で

```sh
# 別のshellで
poe sub3
# 別のshellで
poe pub3
```

中身は pub1/sub1 と一緒
