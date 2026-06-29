# gRPC Interface

## 目的

gRPC Interface は、PIXet Pro と MiniPIX 検出器が接続された PC 上で `MiniPixCtrl` を動かし、別プロセスまたは別 PC からネットワーク越しに同じ制御 API を使うための層です。

ローカル API と gRPC API の役割分担は次のとおりです。

| 層 | 役割 |
|---|---|
| `MiniPixCtrl` | PIXet Python API を直接呼ぶ実機制御層 |
| `pixet_grpc_server.py` | `MiniPixCtrl` を gRPC 経由で公開するサーバ |
| `SyncPixetGrpcClient` | 同期型クライアント |
| `AsyncPixetGrpcClient` | 非同期型クライアント |
| DeviceProxy | 他装置と同じモデルで扱うための登録層 |

## 公開 API

`MiniPixCtrl` を基準に、gRPC 経由で公開する主な API は次のとおりです。

| API | 内容 | 戻り値の目安 |
|---|---|---|
| `connect()` | PIXet core 起動と検出器接続 | `bool` |
| `disconnect()` | PIXet core 終了 | `None` |
| `set_mode_all(mode)` | 全ピクセルの測定モード設定 | `bool` |
| `set_threshold(threshold_kev)` | しきい値設定 | `bool` |
| `set_clock(clock_mhz)` | Timepix clock 設定 | `bool` |
| `set_bias(bias_volt)` | バイアス電圧設定 | `bool` |
| `simple_acq(...)` | 通常 frame モードで撮像 | `dict` または `False` |
| `get_acq_frame_count()` | 保持フレーム数取得 | `int` |
| `get_acq_frames(idx=None)` | 保持フレーム取得 | `dict` |

## 典型的な制御シーケンス

```python
pix.connect()
pix.set_mode_all("TOT")
pix.set_threshold(6.0)
pix.set_bias(150.0)
pix.set_clock(9.66667)
result = pix.simple_acq(1, 3.0, "example.png", "PNG")
pix.disconnect()
```

## データ返却形式

`simple_acq()` と `get_acq_frames()` は、フレームデータを dict として返します。

```python
{
    "frame_count": 1,
    "frames": [
        {
            "name": "frame",
            "width": 256,
            "height": 256,
            "data": [...],
            "subframes": []
        }
    ]
}
```

gRPC 経由ではこの dict がシリアライズされます。`data` はピクセル数分の list になるため、測定条件によっては応答サイズが大きくなります。

## 実装上の注意

`MiniPixCtrl` は PIXet core と実検出器を直接操作します。そのため、gRPC サーバ側では同時実行制御が必要です。特に次の操作は逐次実行にしてください。

・ `connect()` / `disconnect()`  
・ `set_mode_all()`  
・ `set_threshold()`  
・ `set_clock()`  
・ `set_bias()`  
・ `simple_acq()`  

複数クライアントから同時に設定変更や撮像を行うと、検出器状態と戻り値の対応が崩れる可能性があります。

## 未実装 API の扱い

`pixet_ctrl.py` では `get_acq_data_count()`、`get_acq_data()`、`simple_int_acq()` が未実装です。gRPC 側でこれらを公開しても実処理は行われません。現時点の公開対象からは外す方針が安全です。
