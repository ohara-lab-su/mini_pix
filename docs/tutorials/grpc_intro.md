# gRPC チュートリアル

このページでは、`MiniPixCtrl` を gRPC サーバ側に置き、別プロセスまたは別 PC から MiniPIX を制御する構成を説明します。

現状の `pixet_ctrl.py` はローカルの `pypixet` を直接呼ぶ実装です。gRPC 化する場合、PIXet Pro と検出器が接続された Windows PC 上でサーバを起動し、利用者プログラムはクライアントとしてアクセスします。

## 基本方針

```text
Client Script
    │
    ▼
gRPC Client
    │
    ▼
gRPC Server on detector PC
    │
    ▼
MiniPixCtrl
    │
    ▼
pypixet / PIXet core
    │
    ▼
MiniPIX Detector
```

この構成では、PIXet API の DLL / `.pyd` の依存関係はサーバ側だけに置きます。クライアント側は PIXet Pro を直接 import しません。

## サーバ側で公開する制御クラス

サーバ側の制御対象は `MiniPixCtrl` です。

```python
from mini_pix.pixet_ctrl import MiniPixCtrl

ctrl = MiniPixCtrl(logger=logger)
ctrl.connect()
```

公開対象として有用なメソッドは次のとおりです。

・ `connect()`  
・ `disconnect()`  
・ `set_mode_all(mode)`  
・ `set_threshold(threshold_kev)`  
・ `set_clock(clock_mhz)`  
・ `set_bias(bias_volt)`  
・ `simple_acq(count, sec, name, file_type, save_file, return_data)`  
・ `get_acq_frame_count()`  
・ `get_acq_frames(idx=None)`  

`_frame_to_dict()` は内部補助メソッドなので、通常は gRPC 経由で直接公開しません。

## クライアント側の使用イメージ

同期クライアントの使用例です。

```python
from mini_pix.sync_pixet_grpc_client import SyncPixetGrpcClient

pix = SyncPixetGrpcClient("127.0.0.1", 50051)

pix.connect()
pix.set_mode_all("TOT")
pix.set_threshold(6.0)
pix.set_bias(150.0)
pix.set_clock(9.66667)

result = pix.simple_acq(
    count=1,
    sec=3.0,
    name="example.png",
    file_type="PNG",
    save_file=True,
)

pix.disconnect()
```

非同期クライアントを使う場合も、基本的な呼び出し対象は同じです。

## DeviceProxy との関係

DeviceProxy に登録する場合、`MiniPixCtrl` または gRPC クライアントをデバイス実体として扱います。上位アプリケーションからは、ローカル接続か gRPC 接続かを意識せず、同じ制御メソッドを呼ぶ構成を目標にします。

## 注意点

PIXet API と実検出器はサーバ側プロセスでのみ直接扱います。複数クライアントから同時に撮像・設定変更を行うと検出器状態が競合するため、サーバ側で逐次化する構成が必要です。

また、`simple_acq()` の戻り値はフレーム `data` を list として含むため、フレーム数が多い場合は gRPC 応答が大きくなります。大量データ取得では、ファイル保存とメタデータ返却を分ける設計を検討してください。
