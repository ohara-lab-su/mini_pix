# CHANGELOG

## v0.0.2

### 追加

`example/` 以下に MiniPIX の gRPC 通信を使用するサンプルを追加。

- `example/start_minipix_server.py`
  - `pixet_grpc_server` を使用して MiniPIX gRPC デバイスサーバーを起動するサンプル。
  - gRPC サーバーのホスト、ポート、MiniPIX への自動接続、ログレベルを設定可能。

- `example/measure_pixet.py`
  - `DeviceProxy` を使用した最小構成の非同期測定サンプル。
  - `DeviceProxy("mini_pix", ..., async_mode=True)` で非同期 MiniPIX クライアントを生成。
  - 測定モード、しきい値を設定し、`simple_acq()` による測定を実行。

- `example/measure_pixet2.py`
  - `AsyncPixetGrpcClient` を直接使用した、より詳細な非同期測定サンプル。
  - gRPC サーバーへの接続・切断、測定モード、しきい値、バイアス電圧、クロックを設定。
  - `simple_acq()` でフレームデータを取得し、画像をクライアント側に保存。
  - `XLogger` を使用して接続および測定状況をログ出力。
  - `measurement_output/` 以下にタイムスタンプ付きファイル名で測定画像を保存。


## 2026.06.29, v0.0.1, nakada

・ grpc_frame の DeviceProxy に対応
・ mini_pix.server_grpc import 時に MiniPixCtrl を DeviceProxy 登録するように変更
・ DeviceProxy 登録先を ese774_frame ではなく grpc_frame に変更
・ SyncPixetGrpcClient / AsyncPixetGrpcClient を DeviceProxy から生成できるように変更
・ server_grpc/make_pyi.py で grpc_frame.make_pyi_device_proxy を使って __init__.pyi を生成するように変更
・ __init__.pyi は手書きせず、make_pyi.py による生成物として扱う方針に整理

## 2026.03.25, v0.0.0, nakada