# TPMを使う実例

MQTT の認可は、いろいろな事情を考えると、「TPM/SE を使って mTLS」がいいらしいのだが、
具体的にどうするのかがわらない。雰囲気をつかむため ChatGPT に聞いてみた。

```text
Raspberry PI で TPM2.0 を使うMQTTクライアントの場合、どういう手順を踏めばいい?
```

## 全体像

TPM 使う mTLS =  
**秘密鍵をTPM内生成 → 外に出さない → TLSクライアント認証**

流れ

1. TPM セットアップ
2. TPM 内で鍵生成
3. CSR 作成
4. CA 署名 → クライアント証明書
5. MQTT クライアントから「TPM 鍵」で TLS 接続

## 1. 事前

Raspberry Pi + TPM2.0 (I2C/SPI)

パッケージ

```
sudo apt install tpm2-tools tpm2-tss-engine openssl mosquitto-clients
```

TPM 確認

```
tpm2_getcap properties-fixed | head
```

## 2. TPM内で鍵生成

OpenSSL + tpm2-tss-engine 使用

```
export TPM2TSSENGINE_TCTI=device:/dev/tpmrm0

openssl genpkey \
  -engine tpm2tss \
  -algorithm RSA \
  -pkeyopt rsa_keygen_bits:2048 \
  -out client.key
```

ポイント

- 実際の秘密鍵 → TPM 内
- `client.key` → TPM 参照ラッパ

## 3. CSR作成

```
openssl req -new \
  -engine tpm2tss \
  -key client.key \
  -out client.csr \
  -subj "/CN=device001"
```

## 4. CAで署名

自前 CA or AWS IoT など

例(自己 CA)

```
openssl x509 -req \
  -in client.csr \
  -CA ca.crt \
  -CAkey ca.key \
  -CAcreateserial \
  -out client.crt \
  -days 365
```

## 5. MQTT接続 (mosquitto)

Mosquitto CLI は engine 直接弱い → workaround 必要

### 方法A: stunnel経由

TPM 鍵で TLS 終端 → MQTT 平文

`stunnel.conf`

```
client = yes
[mqtts]
accept = 127.0.0.1:1883
connect = broker:8883

engine = tpm2tss
cert = client.crt
key = client.key
CAfile = ca.crt
```

```
stunnel stunnel.conf
mosquitto_pub -h 127.0.0.1 -p 1883 -t test -m hi
```

### 方法B: OpenSSL engine対応クライアント

libmosquitto は engine 非標準  
→ 自作 or Paho + OpenSSL カスタム

## 6. 実運用(重要)

### デバイスID

- CN or SAN に device-id

### CA管理

- デバイス専用証明書(1 台 1 枚)

### revocation

- CRL or Broker 側 deny list

## 7. TPM使う意味

- 秘密鍵抽出不可
- 物理デバイスにバインド
- stolen SD カード無意味

## 8. 改善パターン(実戦)

### PKCS#11使う方が楽

tpm2-pkcs11

```
sudo apt install tpm2-pkcs11
```

→ 多くの MQTT クライアント対応

## 最短構成

```
tpm2-tools
tpm2-tss-engine
openssl
stunnel
mosquitto-clients
```

## よくわからん

Raspberry Pi + TPM2.0 クラスだと
stunnel を使って
MQTT クライアントは localhost:1883 へつないで
stunnel が TSL/mTLS して broker:8883 へつなぐ
感じらしい。

stunnel はこういう階層で TPM にアクセスできて、

```text
stunnel
  ↓
OpenSSL
  ↓
(engine / provider)
  ↓
tpm2-tss (TSS stack)
  ↓
/dev/tpmrm0
  ↓
TPM
```

[tpm2\-software/tpm2\-tss: OSS implementation of the TCG TPM2 Software Stack \(TSS2\)](https://github.com/tpm2-software/tpm2-tss)
がどうして TPM にアクセスできるのかはよくわからない。
"仕様に従ったバイナリを /dev/tpm0 に書くだけ" らしい。

TPM を勉強するなら
開発用に TPM2.0 デバイスをソフトウエアでエミュレートするものがあるらしい。

- [stefanberger/swtpm: Libtpms\-based TPM emulator with socket, character device, and Linux CUSE interface\.](https://github.com/stefanberger/swtpm)
- [SWTPM と Docker ではじめる TPM アプリケーション開発](https://io.cyberdefense.jp/entry/swtpm_docker/)

あと学習教材

- [TPM\-JS](https://google.github.io/tpm-js/)
- [Trusted Computing 1101: Introductory Trusted Platform Module \(TPM\) usage \| OpenSecurityTraining2](https://p.ost2.fyi/courses/course-v1:OpenSecurityTraining2+TC1101_IntroTPM+2024_v1/about)

## ESP32-S3 の場合

ESP32-S3 での mTLS の現実的な実装。

stunnel は不要で、mbedTLS が ESP-IDF に組み込まれているのでアプリが直接 mTLS を話します。

## ESP32-S3 での mTLS × ハードウェアセキュリティ

### 結論から言うと

**ESP32-S3 には TPM チップはない**ですが、代替手段があります。

### ESP32-S3 のセキュリティ機能

```
ESP32-S3
┌─────────────────────────────────────────┐
│  eFuse(OTP)                           │
│  ┌─────────────────────────────────┐   │
│  │ FLASH_ENCRYPTION_KEY            │   │
│  │ SECURE_BOOT_KEY                 │   │
│  │ (書き込んだら読み出し不可)       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Flash 暗号化(AES-XTS)               │
│  → 秘密鍵をFlashに置いても暗号化される  │
│                                         │
│  Secure Boot                            │
│  → 改ざんされたファームウェアは起動しない│
└─────────────────────────────────────────┘
```

TPM のような「チップ内で署名」はできませんが、**Flash 上の鍵を暗号化して保護**する形になります。

### Raspberry Pi との比較

| 機能         | Raspberry Pi + TPM           | ESP32-S3 単体                |
| ------------ | ---------------------------- | ---------------------------- |
| 秘密鍵の格納 | TPM チップ内(取り出し不可)   | Flash(暗号化)                |
| 署名処理     | TPM 内部で完結               | CPU で処理(鍵はメモリに展開) |
| stunnel      | 使える                       | 使えない(Linux じゃない)     |
| mTLS         | mbedTLS / wolfSSL で直接実装 | mbedTLS 組み込み済み         |
| 物理攻撃耐性 | 強い                         | 中程度                       |

### ESP32-S3 での mTLS の現実的な実装

stunnel は不要で、**mbedTLS が ESP-IDF に組み込まれている**のでアプリが直接 mTLS を話します。

```c
// ESP-IDF での mTLS 設定イメージ
esp_tls_cfg_t cfg = {
    .cacert_pem_buf  = server_ca_pem,      // サーバー検証用CA
    .cacert_pem_bytes = server_ca_pem_len,

    .clientcert_pem_buf  = client_cert_pem, // クライアント証明書
    .clientcert_pem_bytes = client_cert_pem_len,

    .clientkey_pem_buf  = client_key_pem,   // ← ここをどう守るか
    .clientkey_pem_bytes = client_key_pem_len,
};
```

### 秘密鍵の保護戦略(ESP32-S3)

#### 1 Flash 暗号化(最低限やるべき)

```
Flash 暗号化を有効化
  → client_key.pem を Flash に書いても
    AES-XTS で暗号化されて読み出せない

ただし...
  実行時はメモリ上に平文で展開される
  → メモリダンプ攻撃には弱い
```

#### 2 NVS(Non-Volatile Storage)+ Flash 暗号化

```c
// 鍵を NVS に格納(Flash 暗号化と組み合わせる)
nvs_handle_t handle;
nvs_open("tls_keys", NVS_READONLY, &handle);
nvs_get_blob(handle, "client_key", key_buf, &key_len);
```

#### 3 ATECC608(外付けセキュアエレメント)← TPM に最も近い

```
ESP32-S3
    ↓ I2C
ATECC608A/B
┌─────────────────┐
│ 秘密鍵スロット  │  ← 鍵は外に出ない
│ 署名エンジン    │  ← チップ内で ECC 署名
└─────────────────┘
```

これが ESP32 界隈での **TPM 相当品**です。

### ATECC608 を使った場合の mTLS フロー

```
ESP32-S3 アプリ(mbedTLS)
    ↓ 「この鍵で署名して」
ATECC608(I2C経由)
    ↓ チップ内部で ECDSA 署名
    ↓ 署名結果だけ返す
mbedTLS
    ↓ mTLS ハンドシェイク完了
MQTT Broker / IoT Hub
```

Raspberry Pi + TPM + stunnel の構成と**概念的にほぼ同じ**になります。

### セキュリティ強度

```
高  ATECC608 外付け     ← TPM 相当、鍵が外に出ない
    ───────────────────
中  Flash 暗号化 + NVS  ← 現実的な妥協点
    ───────────────────
低  Flash にそのまま置く ← 論外
```

## TPMは遅い

TPM はハードウエアだから早いのかと思ってた...
ソフトウエアエミュレータのほうがはるかに速い。

TPM が遅いのはセキュリティのための意図的な設計でもある。

mTLS ハンドシェイクは接続確立時に 1 回だけなので、
遅くても問題にはならない。
