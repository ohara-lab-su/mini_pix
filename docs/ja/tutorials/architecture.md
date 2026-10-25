# Architecture

<a href="https://ohara-lab-su.github.io/mini_pix/en/tutorials/architecture.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/tutorials/architecture.html">日本語</a>

## 基本構成

`pixet_ctrl.py` の中心は `MiniPixCtrl` です。

```text
User Application
    │
    ▼
MiniPixCtrl
    │
    ▼
pypixet / PIXet Python API
    │
    ▼
PIXet core
    │
    ▼
MiniPIX / Timepix detector
```

`MiniPixCtrl` は PIXet Pro の Python API を薄く包む上位制御層です。接続処理、pixel configuration、検出器パラメータ設定、露光、フレーム取得をまとめています。

## 内部状態

`MiniPixCtrl` は主に次の内部参照を保持します。

・ `_pixet` : `pypixet.pixet` から取得した PIXet core のメインオブジェクト  
・ `_dev` : `pixet.devices()` から取得した検出器オブジェクト。現状は先頭デバイスを使用  
・ `_pixcfg` : `_dev.pixCfg()` から取得した pixel configuration  
・ `_logger` : 外部から渡された logger、または標準 `logging` の logger  

## 接続時の初期化方針

Timepix / MPX2 系では `setOperationMode()` を使わず、pixel configuration 側でピクセルごとの mode を設定します。現状の `connect()` では、接続直後に全ピクセルを `PX_TPXMODE_TOT` に設定し、`setToDevice()` でデバイスへ反映します。

このため、測定モードの変更は `set_mode_all()` 経由で行う設計です。

## フレーム取得の構造

撮像は PIXet の `doSimpleAcquisition()` に委譲します。撮像後、PIXet core 内部に保存された acquisition frame を `acqFrameRefInc()` で取得し、`_frame_to_dict()` で Python の dict に変換します。

```text
doSimpleAcquisition()
    │
    ▼
PIXet internal acquisition frames
    │
    ▼
acqFrameRefInc(idx)
    │
    ▼
_frame_to_dict(frame)
    │
    ▼
{"name", "width", "height", "data", "subframes"}
```

`_frame_to_dict()` は frame 本体だけでなく、取得できる場合は `subFrames()` も読み出します。読み出した frame / subframe は最後に `destroy()` します。

## gRPC 化する場合の位置づけ

ネットワーク越しに使う場合は、`MiniPixCtrl` をサーバ側に置き、gRPC クライアントから同等メソッドを呼び出す構成にします。

```text
Client Program
    │
    ▼
SyncPixetGrpcClient / AsyncPixetGrpcClient
    │
    ▼
gRPC
    │
    ▼
pixet_grpc_server.py
    │
    ▼
MiniPixCtrl
    │
    ▼
PIXet Python API
    │
    ▼
MiniPIX Detector
```

検出器制御は実機に接続されたサーバ側プロセスに閉じ込め、利用者側はクライアント API として扱います。
