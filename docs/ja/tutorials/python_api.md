# Python API — MiniPixCtrl

<a href="https://ohara-lab-su.github.io/mini_pix/en/tutorials/python_api.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/tutorials/python_api.html">日本語</a>

## 初期化と接続

`MiniPixCtrl(logger, log_level=None)` の `logger` は必須であり、`None` を渡すと `ValueError` になります。`log_level` は保持されますが、添付コードではロガーのレベル設定処理には使用されません。`connect() -> bool` は `pypixet.start()` 後、`pixet.devices()[0]` を使用します。デバイスなし・`FileDevice 0` では `False` を返します。デバイス情報をログに出力しますが、**特定シリアル番号による選別はしません**。

`disconnect()` は動作中なら停止を試み、PIXetの終了処理を実行します。`connect()` は測定モード・バイアス・しきい値を自動設定しません。

## 検出器設定

| メソッド | 引数 | 実際の動作 |
|---|---|---|
| `set_mode_all(mode)` | `"Counting"`, `"Energy"`, `"Time"` | それぞれ `PX_TPXMODE_MEDIPIX`, `PX_TPXMODE_TOT`, `PX_TPXMODE_TIMEPIX` に設定し、`setToDevice()` で反映 |
| `set_threshold(threshold_kev)` | keV | `setThreshold(0, value, PX_THLFLG_ENERGY)` |
| `set_clock(clock_mhz)` | MHz | `setTimepixClock(value)` |
| `set_bias(bias_volt)` | V | `setBias(value)` |

各設定メソッドは成功時 `True`、SDKエラー時 `False` を返します。校正記録の工場設定（Timepix Clock 10.0 MHz、5 keV付近のTHL約691）を、接続時にこのクラスが自動再現するわけではありません。

## 測定API

```python
acquire(count, sec, acquisition_type="frames", callback=None,
        save_format=None, save_path=None)
acquire_frames(count, sec, callback=None, save_format=None, save_path=None)
acquire_integral(count, sec, callback=None, save_format=None, save_path=None)
```

`count` はSDKへ渡す測定回数、`sec` は1回の測定時間（秒）です。`acquisition_type` は `frames` または `integral` のみ。測定は同期的に実行されます。Framesではcallback/TIFF/HDF5保存時に完了イベントから各フレームを取得し、それ以外は終了後に履歴を読みます。IntegralではPIXetの `doSimpleIntegralAcquisition()` を使用し、Pythonで積算しません。Integralの `frame_count` は**積算結果の保存枚数**であり、`requested_count` と同義ではありません。

返却辞書は `rc`、`acquisition_type`、`frame_count`、`frames`、`saved_file` を含みます。`frames` の要素には `name`、`width`、`height`、`data`（NumPy配列）、`minimum`、`maximum`、`nonzero`、`subframes` が入ります。`data` はJSON配列ではありません。

## 履歴・状態・停止

| メソッド | 意味 |
|---|---|
| `get_frame_count()` | Python側履歴のフレーム数 |
| `get_frame(index)` | Python側履歴の指定フレーム |
| `get_frames()` | 履歴リストの浅いコピー |
| `get_current_frame()` | 最後に保持したフレーム、なければ `None` |
| `clear_frames()` | Python側履歴を消去 |
| `get_acq_frame_count()` | PIXet SDK側の取得フレーム数 |
| `get_acq_frames(idx=None)` | SDK側の全フレームまたは指定フレーム |
| `stop()` | 実行中なら `abortOperation()` |
| `is_running()` / `is_aborting()` | SDK側の動作状態 |
| `state()` | 状態、要求数、完了数、履歴数、直近エラー |

`state()["finished_count"]` はFramesでは保持フレーム数ですが、Integralの成功時は要求回数 `count` が設定されます。`state()["frame_count"]` と混同しないでください。`stop()` を別スレッドから呼ぶ場合の安全性は実機で確認が必要です。

## 保存と例外

`save_format` は `NONE`、`TIFF`、`HDF5`、`PIXET_NATIVE`（大小文字を正規化）です。`"PIXET NATIVE"` も受け付けます。TIFFは `frame_000001.tiff` の形式で個別保存し、HDF5は `frames` データセットに追記してflushします。Integralでは最終フレームだけ保存します。PIXet native保存はSDKへファイル名と `PX_FTYPE_AUTODETECT` を渡します。SDKが生成するネイティブファイルの内部形式は本クラスでは規定しません。

`save_path` 欠落や未対応形式では `ValueError`、未接続では `RuntimeError`、SDK測定失敗時は通常 `RuntimeError` が発生します。`callback` 内の例外も伝播する可能性があります。

出典: 添付 `pixet_ctrl.py`（コードは変更していません）。

測定結果の詳細は [データ構造と取得タイミング](../manual/frame_data.md) を参照。
