# gRPC経由のPython API

<a href="https://ohara-lab-su.github.io/mini_pix/en/tutorials/grpc.html">English</a>

`grpc_frame` はローカル制御APIを透過的に呼び出す通信基盤であり、検出器固有の操作は追加しません。利用可能な検出器制御は `MiniPixCtrl` の公開メソッドを基準とします。

| 用途 | ローカルPython API |
|---|---|
| 接続 | `connect()` / `disconnect()` |
| 設定 | `set_mode_all()` / `set_threshold()` / `set_clock()` / `set_bias()` |
| フレーム測定 | `acquire_frames(count, sec, ...)` |
| 積算測定 | `acquire_integral(count, sec, ...)` |
| 共通測定 | `acquire(count, sec, acquisition_type="frames", ...)` |
| データ参照 | `get_frame()` / `get_frames()` / `get_acq_frames()` |
| 状態・停止 | `state()` / `stop()` / `is_running()` |

`acquire_frames()` と `acquire_integral()` は共通の `acquire()` を呼び出します。測定結果の辞書には `frames`、`frame_count`、`saved_file` などが含まれます。`set_mode_all()` でToT測定を指定する値は `"Energy"` です。

通信サーバーとクライアントの実装ソースがこの資料には含まれないため、具体的な接続コードやクライアントクラス名は検証済みの実行例として掲載しません。
