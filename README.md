# mqtt-learn1

[paho\-mqtt](https://pypi.org/project/paho-mqtt/) v2
の練習

- 実行環境: uv + Python 3.12 + Poe The Poet
- ブローカー(MQTT サーバ): Docker compose で Eclipse Mosquitto

## 開始方法

uv と Docker が必要。

```sh
uv sync
. .venv/bin/activate
```

また

```sh
cp .env-template .env
```

して中身を編集。
おおむねそのままで使用可能。

## 第1系統 - 生 MQTT

[paho\-mqtt · PyPI](https://pypi.org/project/paho-mqtt/) の
"Getting Started" にある
Subscriber example / publisher example ほぼそのまま。

```sh
poe mqtt # MQTTブローカ起動
poe logs # ログを標準出力に表示
# 別のshellで
poe sub1
# 別のshellで
poe pub1
```

2 個メッセージを受けたら、sub1 は終了する。

また fan-out (pub が 1 個で、受ける sub が 2 個以上) の実験として

```sh
poe sub1
# 別のshellで
poe sub1
# 別のshellで
poe pub1
```

もやってみて。
終わったら

```sh
poe down # MQTTブローカ止める
```

## (参考) Broker Status を mqtt-client 取得する実験

事前に
`sudo apt install mosquitto-clients`
が必要
(TODO: コンテナ内の mosquitto_sub を使ってみる)

```sh
poe mqtt
poe uptime  # ctrl+cで終了。デフォルトでは10秒ごとにpublishしてる
#
poe clients # 変化がないとpublishしてこない
```

`$SYS/` のトピックはブローカによって異なる。
Eclipse Mosquitto の場合
<https://mosquitto.org/man/mosquitto-8.html>
の "Broker Status" の章を参照

## 第2系列 - すこし MQTT クライアントっぽい client2

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

## 第3系列 - ブローカをTLS対応にして、8883/TCPで待ち受ける

### (参考) サーバー証明書

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
poe mqtt3
poe logs3
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
poe down3	# ブローカを止める
```

### (参考) サーバ証明書のメモ

以下のような SAN を持つ汎用サーバ証明書を作っています。

```conf
DNS: localhost
DNS: *.nip.io
DNS: *.sslip.io
IP: 127.0.0.1
IP: ::1
```

参考: [nip\.io / sslip\.ioへようこそ](https://sslip.io/)

.env の BROKER_HOST でローカル以外の IP を指定する場合は、
`192-168-1-1.sslip.io` のように指定してください。
(`.`を`-`に置き換える)

## 第4系統 - MQTT over TLS ユーザ名/パスワードつき

### 準備

pub4 と sub4 で使うユーザ名/パスワードを以下の環境変数経由で設定する。
`.env` に書くことを想定。

```conf
# 例。
PUB4_USER=mqtt_pub4
PUB4_PASS=xxxxxxxxxxxxxxxxxxx
SUB4_USER=mqtt_sub4
SUB4_PASS=zzzzzzzzzzzzzzzzzzz
```

設定後

```sh
scripts/gen_passwdfile.sh
```

を実行すると、Docker イメージ内の `mosquitto_passwd` コマンドを使って
`docker/4/mosquitto/config` ファイルを生成します。

### 実行

```sh
poe mqtt4
poe logs4
```

で

```sh
# 別のshellで
poe sub4
# 別のshellで
poe pub4
```

中身は pub1/sub1 と一緒。終わったら

```sh
# ブローカを止める
poe down_tls4
```

### (参考) MQTTのログに関するメモ

ログにこんな警告が出る。

```text
mqtt-tls4  | 1779783015: Warning: File /mosquitto/config/passwd has world readable permissions. Future versions will refuse to load this file.
mqtt-tls4  | To fix this, use `chmod 0700 /mosquitto/config/passwd`.
mqtt-tls4  |
mqtt-tls4  | 1779783015: Warning: File /mosquitto/config/passwd owner is not mosquitto. Future versions will refuse to load this file.To fix this, use `chown mosquitto /mosquitto/config/passwd`.
mqtt-tls4  |
mqtt-tls4  | 1779783015: Warning: File /mosquitto/config/passwd group is not mosquitto. Future versions will refuse to load this file.
```

これ回避策がなさそうなので放置。named volume にすればいいかも。

eclipse mosquotto にユーザー/パスワード認証で接続すると

> 1779783692: New client connected from 172.18.0.1:45278 as auto-148479D3-A076-74DE-6F3D-0CBDEBC76037 (p4, c1, k60, u'sub4').

のようなログがのこる。sub4 はユーザ名。のこりは

#### `p`

- `p4` = MQTT 3.1.1
- `p5` = MQTT 5.0

#### `c`

- `c1` = clean session / clean start が有効
- `c0` = セッションを保持したい接続

#### `k`

- `k30` = keepalive 30 秒
- `k60` = keepalive 60 秒
- `k0` = keepalive 無効（クライアント依存で見かけることあり）

#### TODO: クライアント ID

MQTT で"クライアント ID" というものがあるので調べる。
上の `auto-148479D3-A076-74DE-6F3D-0CBDEBC76037` のところ
