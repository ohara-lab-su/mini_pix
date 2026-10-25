# mini_pixの構成と実装境界

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/architecture.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/architecture.html">日本語</a>

## 実装済みの制御経路

```text
Python application → MiniPixCtrl → pypixet / PIXet core → MiniPIX D08-W0313
```

添付 `pixet_ctrl.py` はPIXet SDKを直接呼び出すローカル制御層であり、gRPC通信を内部で実行しない。実機D08-W0313はTimepix・Si 500 µmセンサーで、個体校正値はメーカーの校正記録に従う。`connect()` は検出された先頭のデバイスを使い、D08-W0313をシリアル番号で自動選択しない。

## 設計上の拡張経路（未確認）

```text
Application → DeviceProxy → gRPC client → gRPC server → MiniPixCtrl → PIXet
```

従来のドキュメントにあるgRPCとDeviceProxyの層は、拡張可能なアーキテクチャとして残す。今回の添付ソースではそれらの実装を確認できないため、**ローカルAPI実装済み**と**上位層の設計案・未確認**を区別する。

## データと制御

`acquire_frames()` はPIXetのフレーム測定、`acquire_integral()` はPIXetの積算測定を利用する。測定結果はPythonの辞書とNumPy配列を含む。HDF5/TIFFの保存はローカルクラスで扱うが、ネットワーク転送や遠隔排他制御はこのクラスの責務ではない。

今後gRPC等を追加する場合も、検出器のモード・しきい値・バイアスの単位、測定結果のデータ型をローカルAPIに合わせる。未実装機能の詳細は [gRPCサーバー](grpc_server.md) と [DeviceProxy](device_proxy.md) を参照。

## gRPCの透過性とローカルAPI

`grpc_frame` はローカル制御APIを透過的に呼び出すための通信基盤であり、**検出器制御機能を独自に追加しません**。したがって、リモートから実行可能な検出器操作は、サーバー側のローカル制御クラスに実装された操作に限られます。RPCの公開名や引数がローカルメソッドと一致するかは、対応するクライアント・サーバーのソースコードによる確認が必要です。

現行の正式なAPIは `pixet_ctrl.py` の `MiniPixCtrl` を基準とします。ローカル制御に存在しない機能を、gRPCだけで提供できるものとして記述しません。通信層の実装状況についても、`pixet_ctrl.py` だけでは断定しません。
