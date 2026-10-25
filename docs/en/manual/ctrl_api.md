# MiniPixCtrl public API

<a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/ctrl_api.html">日本語</a>

This page documents the actual supplied **`pixet_ctrl.py` implementation**. `MiniPixCtrl` requires a `logger`. The public methods and defaults are:

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

Types are abbreviated for readability; consult the generated API reference for complete signatures. Local frame history and PIXet's internal acquisition-frame count are distinct interfaces. `get_frame(index)` accesses local history, whereas `get_acq_frames(idx)` reads the SDK acquisition data.

This page **does not specify a gRPC public API**. Source: supplied `pixet_ctrl.py`.

For return values, NumPy arrays, SDK history, and callback timing, see [Measurement result data](frame_data.md).
