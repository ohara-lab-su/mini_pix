# CHANGELOG

## v0.1.0 - 2026-10-01

v0.1.0 は、現在の MiniPIX 制御・gRPC 通信・VIEW
を今後の開発基準とする最初の基準版です。

### v0.0.x からの再設計

- v0.0.4 までに Frames / Integral、DeviceProxy、gRPC client
  などを実装し、次版を v0.0.5 とする想定で開発を継続していた。
- それまでの確認にはX線を入れない試験が含まれ、API/通信の成功と検出器画像の正しさを十分に分離して検証できていなかった。
- X線を入れて公式 PIXet Pro GUI と Python API を比較したところ、Python
  側が GUI の画像挙動を再現していないことが判明した。
- 旧実装への継ぎ足しを中止し、PIXet Python API
  の最小ローカルコードから制御系を再構築した。
- `01a.py` → `01b_tiff.py` / `01b_gui_memory.py` → `01c_gui_memory.py` →
  `01d_gui_function.py` → `01e_gui_class.py` → `01f_gui_callback.py` →
  `01g_gui_save_intAcq.py` と、raw frame、表示、複数 frame、制御
  class、callback、保存、Integral を段階的に検証した。
- 検証済みローカル実装を `MiniPixCtrl` / `view_local.py`
  に整理し、その後 gRPC server/client と `view_client.py` を接続した。
- この再設計後の実装を v0.1.0 とし、以後の基準版とした。

### Calibration / configuration

- 対象実機を MiniPIX D08-W0313 / serial 2746 / Timepix / Si 500 µm
  として確認。
- 公式 PIXet Pro GUI の Counting / 2.4 keV / 150 V / 9.66667 MHz / 1 s
  を実機画像の基準条件として確認。
- Python API の初期状態では、X線照射時の画像が公式 GUI
  の挙動を再現しなかった。
- 付属USBの `Calibration/MiniPIX-D08-W0313.xml` を API_PIXet_Pro_1.8.3
  の `factory/` に配置。
- 配置後、Python API の取得画像が公式 GUI
  の挙動をほぼ再現することを確認。
- `factory` の個体初期設定と、PIXet
  が終了時に生成・更新して次回優先ロードする `configs` を区別。
- GUI 側 XML と Python API 側 XML
  には実際に差があるため、両者を同一ファイルとして扱わない。
- 以後、API/通信成功だけでなく、公式 GUI
  と同じ実機・条件でのX線画像比較を実機検証基準とした。

### Local validation sequence

- `01a.py`: 最小 acquisition。
- `01b_tiff.py`: memory raw frame と raw TIFF。
- `01b_gui_memory.py`: raw/display 分離とローカル表示。
- `01c_gui_memory.py`: device 処理の関数分離。
- `01d_gui_function.py`: 複数 frame 取得。
- `01e_gui_class.py`: GUI 非依存 control class。
- `01f_gui_callback.py`: `PX_EVENT_ACQ_FINISHED` callback。
- `01g_gui_save_intAcq.py`: 保存、Stop/state、PIXet Integral を統合。

### Verified

- MiniPIX / PIXet
  を接続したサーバーと別マシンのクライアント間で通信を確認。
- `example/view_client.py` によるリモート VIEW の動作を確認。
- `example/measure_simple.py` による Frames 測定を確認。
- `example/measure_integral.py` による Integral 測定を確認。

### MiniPixCtrl

- PIXet 制御本体を `MiniPixCtrl` に整理。
- gRPC、GUI、server/client 設定を `MiniPixCtrl` から分離。
- `connect()` / `disconnect()` による明示的な PIXet 接続管理に対応。
- detector mode、threshold、bias、Timepix clock の設定 API を実装。
- detector mode の公開名を PIXet Pro GUI に合わせて `Counting` /
  `Energy` / `Time` に統一。
- 共通測定 API `acquire()` を実装。
- Frames 用 `acquire_frames()` を実装。
- Integral 用 `acquire_integral()` を実装。
- Integral は PIXet の `doSimpleIntegralAcquisition()` を使用し、Python
  側では積算しない構成に変更。
- `stop()`、`is_running()`、`is_aborting()`、`state()` を実装。
- 測定結果を内部履歴として保持し、`get_frame_count()`、`get_frame()`、`get_frames()`、`get_current_frame()`
  から取得可能にした。
- PIXet acquisition memory を直接参照する `get_acq_frame_count()` /
  `get_acq_frames()` を実装。
- frame size を固定値にせず、frame/device
  情報から取得し、取得できない場合は pixel count
  から判定する構成にした。
- frame data を NumPy 2D array として保持し、minimum / maximum / nonzero
  / subframes を含む辞書形式へ変換するようにした。

### Acquisition callback / streaming

- Frames 測定で PIXet の `PX_EVENT_ACQ_FINISHED` を利用した逐次 callback
  に対応。
- Integral 測定では最終積算フレームのみ callback する構成にした。
- gRPC streaming 用 `_MiniPixStream` を追加。
- acquisition を worker thread で実行し、callback で受け取った frame を
  queue 経由で `grpc_frame` の `StreamCall` へ渡す構成にした。
- Frames / Integral の両方を `StreamCall` で転送可能にした。

### Saving

- server-side save として `TIFF` / `HDF5` / `PIXET_NATIVE` に対応。
- TIFF は表示用変換を行わず、取得した raw 数値配列を1 frame 1
  fileで保存するようにした。
- HDF5 は取得 dtype を維持し、Frames 測定では frame ごとに追記して
  `flush()` するようにした。
- Integral の HDF5 保存は最終積算フレームを保存する構成にした。
- Sync / Async gRPC client に client-side save を実装。
- client-side TIFF は raw 数値配列を保存。
- client-side PNG は表示用の 16 bit grayscale とし、各 frame を min-max
  正規化して保存。
- 複数 frame の client-side 保存では連番ファイル名を生成するようにした。

### gRPC client / DeviceProxy

- `SyncPixetGrpcClient` と `AsyncPixetGrpcClient` を実装。
- `grpc_frame.DeviceProxy` から MiniPIX client を生成可能にした。
- DeviceProxy 名 `mini_pix` と alias `pixet` / `MiniPix` / `MiniPixCtrl`
  / `pixet_grpc` を登録。
- `timeout_sec` と互換引数 `set_timeout_sec` に対応。
- `server_grpc/__init__.py` の import 境界を修正。
- client-only 環境で `mini_pix.server_grpc` を import しても
  `pixet_grpc_server -> MiniPixCtrl -> pypixet`
  を読み込まないよう、server 実装を遅延 import に変更。
- これにより、リモート client は PIXet Python API / `pypixet`
  を必要としない構成にした。

### VIEW

- `view_local.py` を追加し、`MiniPixCtrl` callback を使った完全ローカル
  VIEW に対応。
- `view_client.py` を追加し、別マシンからの gRPC VIEW に対応。
- Frames / Integral の切り替えに対応。
- gRPC `StreamCall` から受信した frame を client 側履歴として保持。
- slider および前後ボタンによる取得済み frame の参照に対応。
- Auto / Manual display range に対応。
- nearest / smooth 表示切り替えに対応。
- Stop 操作に対応。
- 表示処理と raw detector data を分離。

### Examples

- `start_minipix_server.py` を現在の gRPC server 起動方法に更新。
- `measure_simple.py` を `DeviceProxy` + `acquire_frames()` を使用する
  Frames 測定例に更新。
- `measure_integral.py` を `DeviceProxy` + `acquire_integral()`
  を使用する Integral 測定例に更新。
- `mini_pix.yaml` から server/client 共通設定を読み込む構成にした。

### Type hints / public API

- `make_pyi.py` の生成対象を Sync / Async gRPC client の `.pyi` に限定。
- `__init__.py` / `__init__.pyi` を公開 API
  として管理し、自動生成による上書きを行わない構成にした。
- client 側で上書きする `acquire_frames()` / `acquire_integral()` と
  client 固有メソッドを生成 `.pyi` に反映する補正処理を追加。

## v0.0.4

### 追加

- Integral 測定モードに対応しました。
- Integral 測定用の `simple_int_acq()` を追加しました。
- Integral 測定では Pixet API の `doSimpleIntegralAcquisition()`
  を使用し、複数フレームを1枚のフレームとして積算します。
- Integral 測定用のサンプル `measure_integral.py` を追加しました。

### 測定モード

- `simple_acq()`：Pixet Pro の `Frames` に対応する通常のフレーム測定。
- `simple_int_acq()`：Pixet Pro の `Integral` に対応する積算測定。

## v0.0.3 - 2026-09-29

### Changed

- `mini_pix.server_grpc` から `DeviceProxy` を直接 import
  できるように公開 API を修正した。

  - `grpc_frame.DeviceProxy` を `mini_pix.server_grpc` で import。
  - `DeviceProxy` を `__all__` に追加。
  - `from mini_pix.server_grpc import DeviceProxy` を利用可能にした。

- `make_pyi.py` の責務を gRPC client の stub 生成のみに整理した。

  - 自動生成対象を `sync_pixet_grpc_client.pyi` と
    `async_pixet_grpc_client.pyi` に限定。
  - 手書きの公開 API である `__init__.py` / `__init__.pyi`
    を自動生成対象から除外。
  - `__init__.py` を再生成して既存の公開 API
    定義を上書きする問題を修正。
  - client 実装固有の `simple_acq` および補助メソッドについて、生成後の
    `.pyi` を補正する構成に整理。

## 2026-09-29

### Changed

- `MiniPixCtrl.set_mode_all()` の指定名を PIXet Pro の GUI
  `Detector Settings -> Mode` の表示に合わせた。
  - `Counting` -\> `PX_TPXMODE_MEDIPIX`
  - `Energy` -\> `PX_TPXMODE_TOT`
  - `Time` -\> `PX_TPXMODE_TIMEPIX`
- `set_mode_all()` の引数を `Counting` / `Energy` / `Time` に統一し、
  GUI に表示されない `ONEHIT` を公開指定から外した。
- `set_mode_all()` の docstring と不正値時のエラーメッセージを、 上記の
  GUI 表記に合わせて更新した。
- 実行例のモード指定を `ctrl.set_mode_all("Counting")` に変更した。

## v0.0.2

### 追加

`example/` 以下に MiniPIX の gRPC 通信を使用するサンプルを追加。

- `example/start_minipix_server.py`

  - `pixet_grpc_server` を使用して MiniPIX gRPC
    デバイスサーバーを起動するサンプル。
  - gRPC サーバーのホスト、ポート、MiniPIX
    への自動接続、ログレベルを設定可能。

- `example/measure_pixet.py`

  - `DeviceProxy` を使用した最小構成の非同期測定サンプル。
  - `DeviceProxy("mini_pix", ..., async_mode=True)` で非同期 MiniPIX
    クライアントを生成。
  - 測定モード、しきい値を設定し、`simple_acq()` による測定を実行。

- `example/measure_pixet2.py`

  - `AsyncPixetGrpcClient`
    を直接使用した、より詳細な非同期測定サンプル。
  - gRPC
    サーバーへの接続・切断、測定モード、しきい値、バイアス電圧、クロックを設定。
  - `simple_acq()`
    でフレームデータを取得し、画像をクライアント側に保存。
  - `XLogger` を使用して接続および測定状況をログ出力。
  - `measurement_output/`
    以下にタイムスタンプ付きファイル名で測定画像を保存。

## 2026.06.29, v0.0.1, nakada

・ grpc_frame の DeviceProxy に対応 ・ mini_pix.server_grpc import 時に
MiniPixCtrl を DeviceProxy 登録するように変更 ・ DeviceProxy 登録先を
ese774_frame ではなく grpc_frame に変更 ・ SyncPixetGrpcClient /
AsyncPixetGrpcClient を DeviceProxy から生成できるように変更 ・
server_grpc/make_pyi.py で grpc_frame.make_pyi_device_proxy を使って
**init**.pyi を生成するように変更 ・ **init**.pyi
は手書きせず、make_pyi.py による生成物として扱う方針に整理

## 2026.03.25, v0.0.0, nakada
