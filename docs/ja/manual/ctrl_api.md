# MiniPixCtrl 公開API

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/ctrl_api.html">English</a>

このページは添付された **`pixet_ctrl.py` の実装**を対象とする。`MiniPixCtrl` の初期化には `logger` が必須である。メソッドの引数名と既定値は以下のとおり。

```text
MiniPixCtrl(logger, log_level=None)
connect() -> bool
disconnect()
set_mode_all(mode: str) -> bool
set_threshold(threshold_kev: float) -> bool
set_clock(clock_mhz: float) -> bool
set_bias(bias_volt: float) -> bool
acquire(count: int, sec: float, acquisition_type: str = "frames",
        callback=None, save_format=None, save_path=None) -> dict
acquire_frames(count: int, sec: float, callback=None,
               save_format=None, save_path=None) -> dict
acquire_integral(count: int, sec: float, callback=None,
                 save_format=None, save_path=None) -> dict
clear_frames()
get_frame_count() -> int
get_frame(index: int) -> dict
get_frames() -> list
get_current_frame() -> dict | None
get_acq_frame_count() -> int
get_acq_frames(idx=None) -> dict
stop()
is_running() -> bool
is_aborting() -> bool
state() -> dict
```

上記の型は読みやすさのため簡略表記したものであり、完全な型シグネチャは自動生成APIリファレンスを参照すること。フレーム履歴の取得とPIXet内部の取得フレーム数の参照は異なるAPIである。`get_frame(index)` はローカル履歴を参照する。`get_acq_frames(idx)` はSDK側の取得結果を参照する。

このページは**gRPC公開APIを説明するものではない**。出典：添付 `pixet_ctrl.py`。

詳細な戻り値、NumPy配列、SDK履歴との区別、callbackのタイミングは [測定結果のデータ構造](frame_data.md) を参照。
