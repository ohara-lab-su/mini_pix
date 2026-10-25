# gRPCサーバーとローカル制御の関係

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/grpc_server.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/grpc_server.html">日本語</a>

## 実装確認の範囲

`MiniPixCtrl` は `pixet_ctrl.py` に実装されたローカル制御クラスである。`connect()`、設定、測定、停止、フレーム取得、状態取得は確認できる。一方、**今回確認したソースは `pixet_ctrl.py` のみ**であり、gRPCサーバー実装・RPC定義の有無をプロジェクト全体について断定しない。

## 想定する構成（設計資料・実装未確認）

```text
Remote client → gRPC server → MiniPixCtrl → pypixet / PIXet → MiniPIX D08-W0313
```

過去のドキュメントに記載された `pixet_grpc_server.py`、`SyncPixetGrpcClient`、`AsyncPixetGrpcClient` は**構想または別ソースに存在する可能性のあるコンポーネント**として残す。添付ソースからはクラスの存在、RPC名、ポート番号、実行例の動作を確認できないため、実装済みAPIとして扱わない。

## 公開を検討するローカルAPI

| 用途 | `MiniPixCtrl` の確認済みメソッド | gRPC公開状況 |
|---|---|---|
| 接続 | `connect()` / `disconnect()` | 未確認 |
| 設定 | `set_mode_all()` / `set_threshold()` / `set_clock()` / `set_bias()` | 未確認 |
| 測定 | `acquire()` / `acquire_frames()` / `acquire_integral()` | 未確認 |
| 中断・状態 | `stop()` / `is_running()` / `is_aborting()` / `state()` | 未確認 |
| 画像 | `get_frame()` / `get_frames()` / `get_acq_frames()` | 未確認 |

画像データはNumPy配列である。gRPC公開時にはshape、dtype、バイトオーダー、フレームサイズ、転送制限、排他制御、切断時の動作を明示する必要がある。**これらは設計課題であり、現行の `MiniPixCtrl` が自動的に提供する機能ではない。**

## gRPCの透過性とローカルAPI

`grpc_frame` はローカル制御APIを透過的に呼び出すための通信基盤であり、**検出器制御機能を独自に追加しません**。したがって、リモートから実行可能な検出器操作は、サーバー側のローカル制御クラスに実装された操作に限られます。RPCの公開名や引数がローカルメソッドと一致するかは、対応するクライアント・サーバーのソースコードによる確認が必要です。

現行の正式なAPIは `pixet_ctrl.py` の `MiniPixCtrl` を基準とします。ローカル制御に存在しない機能を、gRPCだけで提供できるものとして記述しません。通信層の実装状況についても、`pixet_ctrl.py` だけでは断定しません。
