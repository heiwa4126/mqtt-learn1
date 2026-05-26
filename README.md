# mqtt-learn1

[paho\-mqtt](https://pypi.org/project/paho-mqtt/) v2
の練習

- uv + Python 3.12 + Poe The Poet
- Docker compose で Eclipse Mosquitto

## 開始方法

uv と Docker が必要。

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

### サーバー証明書

すでに `var/tls/` 以下に
[trustme · PyPI](https://pypi.org/project/trustme/)
で作った CA とサーバ証明書、5 台分のクライアント証明書があるので
それをそのまま使ってください。

CA の秘密キーがないので、署名はできません。使い捨て CA

なんらかの事情で証明書セットを作り直したいときは

```sh
poe poe tls_certs_force
```

### 実行

```sh
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

3 系統の中身は pub1/sub1 と一緒。終わったら

```sh
# ブローカを止める
poe down_tls
```

### サーバ証明書のメモ

以下のような SAN を持つ汎用サーバ証明書を作っています。

```conf
DNS: localhost
DNS: *.nip.io
DNS: *.sslip.io
IP: 127.0.0.1
IP: ::1
```

[nip\.io / sslip\.ioへようこそ](https://sslip.io/)

.env の BROKER_HOST でローカル以外の IP を指定する場合は、
`192-168-1-1.sslip.io` のように指定してください。
(`.`を`-`に置き換える)

## 
