# フレーム測定と積算測定

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/acquisition.html">English</a>

`MiniPixCtrl.acquire(count, sec, acquisition_type="frames", callback=None, save_format=None, save_path=None)` は共通測定APIである。`count` は測定回数、`sec` は1回の測定時間（秒）を指定する。受け付ける測定種別は `frames` と `integral` のみである。

**Frames:** `doSimpleAcquisition()` を使用する。callback、TIFF保存、HDF5保存のいずれかが有効な場合、`PX_EVENT_ACQ_FINISHED` にフックして各フレームを取得する。それ以外の場合は測定終了後に `acqFrameCount()` と `acqFrame()` を利用して結果を読み出す。取得結果は内部履歴に保持する。

**Integral:** `doSimpleIntegralAcquisition()` を使用する。**Python側でフレームを加算しない**。完了後に最終積算フレームを取得し、callbackがあれば1回だけ呼ぶ。`count` を指定しても、返却される画像数は通常のフレーム測定と同一ではない。

結果の辞書は `rc`、`acquisition_type`、`frame_count`、`frames`、`saved_file` を持つ。`frames` の各要素は画像データとサイズ・統計量を含む。エラー時は例外を発生させ、`state()` からエラー状態を参照できる。

**注意:** `acquire()` は同期呼び出しであり、測定終了まで戻らない。外部から停止する場合は別スレッドなどで `stop()` を呼ぶ設計が必要になる。実機での動作・割り込みの応答性は未検証。

出典：添付 `pixet_ctrl.py` `acquire()`、`acquire_frames()`、`acquire_integral()`。
