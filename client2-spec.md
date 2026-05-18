# client2 設計書

## 概要

MQTT を使った時刻配信クライアント。現在時刻を指定タイムゾーンで配信し、タイムゾーンの変更コマンドを受け付ける。

## デバイス ID

`<ID>` はデバイスを一意に識別する文字列。

| 環境       | 値                           |
| ---------- | ---------------------------- |
| テスト段階 | 起動時のオプション引数で指定 |
| ESP32 など | MAC アドレス                 |

## トピック一覧

| 役割         | 方向 | トピック               | QoS | Retain   |
| ------------ | ---- | ---------------------- | --- | -------- |
| Telemetry    | pub  | `clock/<ID>/telemetry` | 1   | false    |
| Command 受信 | sub  | `clock/<ID>/cmd`       | 1   | —        |
| Command 応答 | pub  | `clock/<ID>/cmd/resp`  | 1   | false    |
| Status 通知  | pub  | `clock/<ID>/status`    | 1   | **true** |

## トピック詳細

### Telemetry

現在時刻を現在のタイムゾーンで ISO 8601 形式にして定期 publish する。

- **pub:** `clock/<ID>/telemetry`
- **interval:** 5 秒
- **QoS:** 1 / **retain:** false

```json
{ "time": "2025-05-18T19:00:00+09:00" }
```

| フィールド | 型     | 説明                                         |
| ---------- | ------ | -------------------------------------------- |
| `time`     | string | 現在時刻(ISO 8601、現在 TZ のオフセット付き) |

### Command

タイムゾーン変更を要求する。

#### リクエスト

- **sub:** `clock/<ID>/cmd`
- **QoS:** 1

```json
{
	"req_id": "550e8400-e29b-41d4-a716-446655440000",
	"tz": "Asia/Tokyo"
}
```

| フィールド | 型            | 必須 | 説明                                                                                    |
| ---------- | ------------- | ---- | --------------------------------------------------------------------------------------- |
| `req_id`   | string (UUID) | ✓    | リクエスト識別子。応答に同値をエコーバックする                                          |
| `tz`       | string        | ✓    | IANA タイムゾーン ID(例: `UTC`, `Asia/Tokyo`, `America/New_York`)。デフォルト値は `UTC` |

#### レスポンス

- **pub:** `clock/<ID>/cmd/resp`
- **QoS:** 1 / **retain:** false

```json
{
	"req_id": "550e8400-e29b-41d4-a716-446655440000",
	"status": "OK"
}
```

```json
{
	"req_id": "550e8400-e29b-41d4-a716-446655440000",
	"status": "ERROR",
	"message": "Unknown timezone: Invalid/Zone"
}
```

| フィールド | 型            | 必須         | 説明                                 |
| ---------- | ------------- | ------------ | ------------------------------------ |
| `req_id`   | string (UUID) | ✓            | リクエストの `req_id` をそのまま返す |
| `status`   | string        | ✓            | `"OK"` または `"ERROR"`              |
| `message`  | string        | エラー時のみ | エラー内容の説明                     |

### Status

現在のタイムゾーン設定を通知する。

- **pub:** `clock/<ID>/status`
- **QoS:** 1 / **retain:** true

```json
{ "tz": "Asia/Tokyo" }
```

| フィールド | 型     | 説明                              |
| ---------- | ------ | --------------------------------- |
| `tz`       | string | 現在設定中の IANA タイムゾーン ID |

## 動作シーケンス

### 起動時

```
client2 起動
  └─► status publish(retain=true)
```

### Command 受信時

#### 正常系(有効な TZ)

```
cmd 受信
  ├─► TZ 更新
  ├─► status publish(retain=true)
  └─► cmd/resp publish(status: "OK")
```

#### 異常系(無効な TZ)

```
cmd 受信
  └─► cmd/resp publish(status: "ERROR", message: エラー内容)
      ※ TZ は更新しない / status は publish しない
```

### Telemetry(定期)

```
5 秒ごと
  └─► 現在 TZ で ISO 8601 生成 → telemetry publish
```

### 複数 Command の処理順序

到着順に逐次処理する(キューイング)。

## タイムゾーン仕様

- 値は IANA タイムゾーン ID を使用する(例: `UTC`, `Asia/Tokyo`, `America/New_York`)
- 無効な値を受け取った場合は TZ を更新せず、`cmd/resp` に `status: "ERROR"` を返す
- 初期値(デフォルト)は `UTC`
