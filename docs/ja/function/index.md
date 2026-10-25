# Python API の構成と実装状況

<a href="https://ohara-lab-su.github.io/mini_pix/en/function/index.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/function/index.html">日本語</a>

このページは `pixet_ctrl.py` の実装と、今後の拡張候補を区別するための案内である。対象実機は **MiniPIX D08-W0313**（Timepix、Si 500 µm）。機器の校正条件はメーカーの個体別校正証明書を参照する。一般的なMiniPIXのデータシート値を、この個体の校正値として流用しない。

## 実装済み：`MiniPixCtrl`

以下のメソッドは添付された `pixet_ctrl.py` に定義されている。これは**ソース上の実装確認**であり、すべての条件での実機試験完了を意味しない。

| 用途 | メソッド |
| --- | --- |
| 初期化・接続 | `__init__(logger, log_level=None)`, `connect()`, `disconnect()` |
| 検出器設定 | `set_mode_all(mode)`, `set_threshold(...)`, `set_clock(...)`, `set_bias(...)` |
| 画像サイズ | `get_frame_size()` |
| フレーム取得・管理 | `clear_frames()`, `get_frame_count()`, `get_frame(...)`, `get_frames(...)`, `get_current_frame()` |
| 測定装置側のフレーム参照 | `get_acq_frame_count()`, `get_acq_frames(...)` |
| 測定 | `acquire(...)`, `acquire_frames(...)`, `acquire_integral(...)` |
| 停止・状態 | `stop()`, `is_running()`, `is_aborting()`, `state()` |

`logger` は必須である。`set_mode_all()` が受け付けるモード文字列は `"Counting"`、`"Energy"`、`"Time"`。`connect()` は検出された最初のデバイスを使用し、D08-W0313の個体番号を自動照合しない。測定の引数・戻り値と保存形式は <a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/ctrl_api.html">制御API</a> と <a href="https://ohara-lab-su.github.io/mini_pix/jp/tutorials/python_api.html">Python API チュートリアル</a> を参照する。

## 未実装または実装未確認

| 名称 | 状態 | 備考 |
| --- | --- | --- |
| `SyncPixetGrpcClient` | 添付コードでは実装未確認 | 同期gRPCクライアントの設計候補。 |
| `AsyncPixetGrpcClient` | 添付コードでは実装未確認 | 非同期gRPCクライアントの設計候補。 |
| `pixet_grpc_server.py` | 添付コードでは実装未確認 | サーバー構成案。 |
| DeviceProxy | 添付コードでは実装未確認 | クライアント側の抽象化案。 |

上記の設計候補は将来の実装検討のために記載を維持する。**実装済みAPIとしてインポート・実行できることは保証しない。**

## 自動生成APIリファレンス

実際にパッケージのソースから生成されるAPIリファレンスは <a href="https://ohara-lab-su.github.io/mini_pix/jp/api/index.html">API Reference</a> を参照する。生成時にはリポジトリの `src/mini_pix` が必要である。
