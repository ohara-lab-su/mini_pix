# 実装状況とAPIの適用範囲

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/implementation_status.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/implementation_status.html">日本語</a>

このページは **Pythonライブラリ `mini_pix` のマニュアル**であり、検出器の製品取扱説明書ではない。実機は **MiniPIX D08-W0313**（Timepix、Si 500 µm、readout serial 2746）である。校正証明書の数値はこの個体の試験結果であり、別個体や将来の測定状態を保証する値ではない。

## 現行実装で確認したAPI

添付 `pixet_ctrl.py` の `MiniPixCtrl` で定義されているメソッドを示す。メソッドが存在することと、全条件で実機動作が検証済みであることは異なる。

| 分野 | 実装済みメソッド | 注意点 |
| --- | --- | --- |
| 接続 | `connect()`, `disconnect()` | `connect()` はD08-W0313の個体番号を照合しない。 |
| 設定 | `set_mode_all()`, `set_threshold()`, `set_clock()`, `set_bias()` | `set_mode_all()` は `Counting` / `Energy` / `Time` のみ。しきい値はkeV指定。 |
| 測定 | `acquire()`, `acquire_frames()`, `acquire_integral()` | `frames` と `integral` を区別する。Integralの積算はPIXet SDKが行う。 |
| 履歴 | `clear_frames()`, `get_frame_count()`, `get_frame()`, `get_frames()`, `get_current_frame()` | Python側に保持した履歴を参照する。 |
| SDK取得 | `get_acq_frame_count()`, `get_acq_frames()` | SDK側のフレームとPython履歴を混同しない。 |
| 状態 | `stop()`, `is_running()`, `is_aborting()`, `state()` | 停止応答時間や全条件のスレッド安全性はこのコードだけでは保証できない。 |

`MiniPixCtrl` のコンストラクタは `logger` を必須引数とする。`acquire()` の `save_format` は `None`、`TIFF`、`HDF5`、`PIXET_NATIVE` を対象とする。保存形式によって出力先の意味が異なるため、詳細は測定と保存の各ページを参照する。

## 通信層の確認範囲

測定APIは `acquire()`、`acquire_frames()`、`acquire_integral()` を正式な公開インターフェースとして扱う。

`grpc_server` と `DeviceProxy` に関する記述は**将来設計または実装未確認**として保持する。今回確認できた `pixet_ctrl.py` 単体では、gRPCサーバー・プロキシの具体的な実装やRPC名を確定できない。これらを `MiniPixCtrl` の実装済みメソッドとして列挙しない。

## 校正資料とAPIの関係

D08-W0313の校正証明書には、5 keVのしきい値に対応するTHL（約691）や、校正時のバイアス試験値が記録されている。`set_threshold(threshold_kev)` の引数は**エネルギー[keV]**であり、THLのDAC値を渡すAPIではない。メーカー試験値をPythonコードの既定値とみなさない。

メーカーPDFは実機の取り扱い・製品仕様・校正の一次資料であり、ここでのPython API仕様の根拠は添付 `pixet_ctrl.py` とする。メーカー資料に存在する操作がPython APIにも実装されているとは限らない。
