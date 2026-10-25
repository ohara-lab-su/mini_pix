# gRPC連携の設計と実装状況

<a href="https://ohara-lab-su.github.io/mini_pix/en/tutorials/grpc_intro.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/tutorials/grpc_intro.html">日本語</a>

## 利用目的

PIXet SDKを導入した検出器接続PCで `MiniPixCtrl` を動かし、別PCから制御する構成を想定する。ローカル制御とネットワーク公開を分離する設計は維持する。

```text
Application → DeviceProxy（構想・実装未確認）
            → gRPC client（実装未確認）
            → gRPC server（実装未確認）
            → MiniPixCtrl（pixet_ctrl.pyで確認済み）
            → pypixet / PIXet → MiniPIX D08-W0313
```

## ローカルで確認できる使用法

```python
import logging
from mini_pix.pixet_ctrl import MiniPixCtrl

logger = logging.getLogger("mini_pix")
ctrl = MiniPixCtrl(logger=logger)
if not ctrl.connect():
    raise RuntimeError("Detector connection failed")
try:
    if not ctrl.set_mode_all("Energy"):
        raise RuntimeError("Mode configuration failed")
    result = ctrl.acquire_frames(count=1, sec=1.0)
finally:
    ctrl.disconnect()
```

上記は**ローカルAPIの使用例**であり、gRPCクライアントの実行例ではない。しきい値・バイアスは実験条件と校正に応じて設定する。

## 将来の拡張

`SyncPixetGrpcClient` / `AsyncPixetGrpcClient`、`pixet_grpc_server.py`、DeviceProxyを利用する構成は従来の設計案として保持する。添付ソースだけでは実装の有無が確定しないため、import例や接続先を捏造しない。通信時の画像シリアライズ、同時操作の排他、停止要求の取り扱いは別途定義する。

## gRPCの透過性とローカルAPI

`grpc_frame` はローカル制御APIを透過的に呼び出すための通信基盤であり、**検出器制御機能を独自に追加しません**。したがって、リモートから実行可能な検出器操作は、サーバー側のローカル制御クラスに実装された操作に限られます。RPCの公開名や引数がローカルメソッドと一致するかは、対応するクライアント・サーバーのソースコードによる確認が必要です。

現行の正式なAPIは `pixet_ctrl.py` の `MiniPixCtrl` を基準とします。ローカル制御に存在しない機能を、gRPCだけで提供できるものとして記述しません。通信層の実装状況についても、`pixet_ctrl.py` だけでは断定しません。
