# DeviceProxyとの統合

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/device_proxy.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/device_proxy.html">日本語</a>

## 目的と確認範囲

DeviceProxyは、ローカル実装とリモートクライアントを上位アプリケーションから同様に操作するための**設計上の抽象化**として従来の文書に記載されている。この構想は削除しない。ただし、今回の `pixet_ctrl.py` にはDeviceProxyの定義がなく、生成関数・登録関数・通信方式の実装確認はできない。

## 想定する責務

- ローカル: `MiniPixCtrl` がPIXet SDKと検出器を直接操作する（**実装確認済み**）。
- リモート: gRPCクライアントがサーバーへ処理を委譲する（**本資料では未確認**）。
- プロキシ: 上位アプリケーションから接続方式を隠蔽する（**設計方針、実装未確認**）。

過去に記載された `register_device` や `DeviceProxy` は**将来実装・別実装の候補**として扱い、実行可能なサンプルコードとはみなさない。対応する実装が確認できた段階で、正確なimport先、コンストラクタ、同期／非同期切り替えを追記する。

## APIの互換性

共通インターフェースの候補は `connect()`、`disconnect()`、`set_mode_all()`、`set_threshold()`、`acquire_frames()`、`acquire_integral()`、`stop()`、`state()` である。**現時点で保証されるのは `MiniPixCtrl` のローカル実装だけ**であり、リモート経由での互換性は未検証である。

## gRPCの透過性とローカルAPI

`grpc_frame` はローカル制御APIを透過的に呼び出すための通信基盤であり、**検出器制御機能を独自に追加しません**。したがって、リモートから実行可能な検出器操作は、サーバー側のローカル制御クラスに実装された操作に限られます。RPCの公開名や引数がローカルメソッドと一致するかは、対応するクライアント・サーバーのソースコードによる確認が必要です。

現行の正式なAPIは `pixet_ctrl.py` の `MiniPixCtrl` を基準とします。ローカル制御に存在しない機能を、gRPCだけで提供できるものとして記述しません。通信層の実装状況についても、`pixet_ctrl.py` だけでは断定しません。
