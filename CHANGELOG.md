# CHANGELOG

## v0.1.0 - 2026-10-01

MiniPIX 実機制御を再検証し、ローカル制御から gRPC リモート測定までを再設計した基準版。

### Changed

-   v0.0.4 の次版として予定していた v0.0.5 の開発中、X線照射下で Python API の取得結果が PIXet Pro GUI の挙動を再現していないことが判明したため、実機制御部分を再設計。
-   PIXet Python API の最小ローカル実装から測定処理を再検証し、検証済み実装を `MiniPixCtrl` に統合。
-   ローカル制御、GUI、gRPC server/client の責務を分離。
-   Frames / Integral の API を `acquire_frames()` / `acquire_integral()` に整理。
-   Integral は PIXet の `doSimpleIntegralAcquisition()` を使用し、Python 側では積算しない構成へ変更。
-   Frames の逐次取得を `PX_EVENT_ACQ_FINISHED` callback で行い、gRPC `StreamCall` によるリモート転送へ接続。
-   raw detector data と表示処理を分離。
-   client-only 環境では PIXet Python API / `pypixet` を必要としない構成へ変更。

### Fixed

-   個体固有の calibration / device configuration が正しくロードされない状態では、Python API の取得画像が PIXet Pro GUI の挙動を再現しない問題を確認。
-   D08-W0313 の個体用 XML を PIXet API の `factory/` から読み込む環境へ修正。
-   `mini_pix.server_grpc` の import 時に server 実装経由で `pypixet` まで import される問題を、server 実装の遅延 import により修正。

### Added

-   TIFF / HDF5 / PIXet native の server-side 保存。
-   TIFF / PNG の client-side 保存。
-   ローカル VIEW `view_local.py`。
-   gRPC リモート VIEW `view_client.py`。
-   Frames 測定例 `measure_simple.py`。
-   Integral 測定例 `measure_integral.py`。
-   `stop()`、測定状態取得、フレーム履歴取得 API。
-   Sync / Async gRPC client と `DeviceProxy` 対応。
-   gRPC client の `.pyi` 生成・補正処理。

### Verified

-   PIXet Pro GUI と Python API の実機X線画像を比較し、個体用 calibration/configuration 適用後の取得画像を確認。
-   MiniPIX / PIXet を接続したサーバーと別マシンのクライアント間で通信を確認。
-   別マシンから `view_client.py` の Frames / Integral 表示を確認。
-   別マシンから `measure_simple.py` による Frames 測定を確認。
-   別マシンから `measure_integral.py` による Integral 測定を確認。

## v0.0.4

### 追加

-   Integral 測定モードに対応しました。
-   Integral 測定用の `simple_int_acq()` を追加しました。
-   Integral 測定では Pixet API の `doSimpleIntegralAcquisition()` を使用し、複数フレームを1枚のフレームとして積算します。
-   Integral 測定用のサンプル `measure_integral.py` を追加しました。

### 測定モード

-   `simple_acq()`：Pixet Pro の `Frames` に対応する通常のフレーム測定。
-   `simple_int_acq()`：Pixet Pro の `Integral` に対応する積算測定。

## v0.0.3 - 2026-09-29

### Changed

-   `mini_pix.server_grpc` から `DeviceProxy` を直接 import できるように公開 API を修正した。

    -   `grpc_frame.DeviceProxy` を `mini_pix.server_grpc` で import。
    -   `DeviceProxy` を `__all__` に追加。
    -   `from mini_pix.server_grpc import DeviceProxy` を利用可能にした。

-   `make_pyi.py` の責務を gRPC client の stub 生成のみに整理した。

    -   自動生成対象を `sync_pixet_grpc_client.pyi` と `async_pixet_grpc_client.pyi` に限定。
    -   手書きの公開 API である `__init__.py` / `__init__.pyi` を自動生成対象から除外。
    -   `__init__.py` を再生成して既存の公開 API 定義を上書きする問題を修正。
    -   client 実装固有の `simple_acq` および補助メソッドについて、生成後の `.pyi` を補正する構成に整理。

## 2026-09-29

### Changed

-   `MiniPixCtrl.set_mode_all()` の指定名を PIXet Pro の GUI `Detector Settings -> Mode` の表示に合わせた。
    -   `Counting` -> `PX_TPXMODE_MEDIPIX`
    -   `Energy` -> `PX_TPXMODE_TOT`
    -   `Time` -> `PX_TPXMODE_TIMEPIX`
-   `set_mode_all()` の引数を `Counting` / `Energy` / `Time` に統一し、 GUI に表示されない `ONEHIT` を公開指定から外した。
-   `set_mode_all()` の docstring と不正値時のエラーメッセージを、 上記の GUI 表記に合わせて更新した。
-   実行例のモード指定を `ctrl.set_mode_all("Counting")` に変更した。

## v0.0.2

### 追加

`example/` 以下に MiniPIX の gRPC 通信を使用するサンプルを追加。

-   `example/start_minipix_server.py`

    -   `pixet_grpc_server` を使用して MiniPIX gRPC デバイスサーバーを起動するサンプル。
    -   gRPC サーバーのホスト、ポート、MiniPIX への自動接続、ログレベルを設定可能。

-   `example/measure_pixet.py`

    -   `DeviceProxy` を使用した最小構成の非同期測定サンプル。
    -   `DeviceProxy("mini_pix", ..., async_mode=True)` で非同期 MiniPIX クライアントを生成。
    -   測定モード、しきい値を設定し、`simple_acq()` による測定を実行。

-   `example/measure_pixet2.py`

    -   `AsyncPixetGrpcClient` を直接使用した、より詳細な非同期測定サンプル。
    -   gRPC サーバーへの接続・切断、測定モード、しきい値、バイアス電圧、クロックを設定。
    -   `simple_acq()` でフレームデータを取得し、画像をクライアント側に保存。
    -   `XLogger` を使用して接続および測定状況をログ出力。
    -   `measurement_output/` 以下にタイムスタンプ付きファイル名で測定画像を保存。

## 2026.06.29, v0.0.1, nakada

・ grpc_frame の DeviceProxy に対応 ・ mini_pix.server_grpc import 時に MiniPixCtrl を DeviceProxy 登録するように変更 ・ DeviceProxy 登録先を ese774_frame ではなく grpc_frame に変更 ・ SyncPixetGrpcClient / AsyncPixetGrpcClient を DeviceProxy から生成できるように変更 ・ server_grpc/make_pyi.py で grpc_frame.make_pyi_device_proxy を使って **init**.pyi を生成するように変更 ・ **init**.pyi は手書きせず、make_pyi.py による生成物として扱う方針に整理

## 2026.03.25, v0.0.0, nakada
