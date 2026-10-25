# Python API — MiniPixCtrl

<a href="https://ohara-lab-su.github.io/mini_pix/en/tutorials/python_api.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/tutorials/python_api.html">日本語</a>

## Initialization and connection

`MiniPixCtrl(logger, log_level=None)` **requires** a logger; `None` raises `ValueError`. `log_level` is stored but is not used to configure the logger in the supplied implementation. `connect() -> bool` calls `pypixet.start()` and selects `pixet.devices()[0]`. It returns `False` for an empty device list or `FileDevice 0`. Device information is logged, but **no serial-number filtering is performed**.

`disconnect()` attempts to stop an active acquisition and shuts down PIXet. `connect()` does not automatically configure mode, bias, or threshold.

## Detector settings

| Method | Argument | Implementation |
|---|---|---|
| `set_mode_all(mode)` | `"Counting"`, `"Energy"`, `"Time"` | Maps to `PX_TPXMODE_MEDIPIX`, `PX_TPXMODE_TOT`, `PX_TPXMODE_TIMEPIX`, then calls `setToDevice()` |
| `set_threshold(threshold_kev)` | keV | `setThreshold(0, value, PX_THLFLG_ENERGY)` |
| `set_clock(clock_mhz)` | MHz | `setTimepixClock(value)` |
| `set_bias(bias_volt)` | V | `setBias(value)` |

Each returns `True` on success and `False` on an SDK error. The class does not automatically reproduce the detector's factory settings (10.0 MHz clock and a THL DAC value around 691 for 5 keV).

## Acquisition API

```python
acquire(count, sec, acquisition_type="frames", callback=None,
        save_format=None, save_path=None)
acquire_frames(count, sec, callback=None, save_format=None, save_path=None)
acquire_integral(count, sec, callback=None, save_format=None, save_path=None)
```

`count` is the acquisition count passed to the SDK; `sec` is the exposure duration per acquisition. Only `frames` and `integral` are accepted. Calls are synchronous. For Frames, a completion event is used when a callback, TIFF, or HDF5 output is requested; otherwise frames are read after acquisition. Integral uses PIXet's `doSimpleIntegralAcquisition()` and **does not sum frames in Python**. Its `frame_count` is the number of stored integrated images, not necessarily the requested count.

The return dictionary includes `rc`, `acquisition_type`, `frame_count`, `frames`, and `saved_file`. Each frame has `name`, `width`, `height`, `data` (a NumPy array), `minimum`, `maximum`, `nonzero`, and `subframes`. `data` is **not** a JSON-ready list.

## Frame history, state, and stopping

| Method | Meaning |
|---|---|
| `get_frame_count()` | Number of frames stored in Python |
| `get_frame(index)` | Indexed Python history frame |
| `get_frames()` | Shallow copy of the history list |
| `get_current_frame()` | Latest frame or `None` |
| `clear_frames()` | Clear Python history |
| `get_acq_frame_count()` | Frame count in the PIXet SDK |
| `get_acq_frames(idx=None)` | All or one frame from the SDK |
| `stop()` | Call `abortOperation()` when running |
| `is_running()` / `is_aborting()` | SDK acquisition state |
| `state()` | State, requested/completed counts, history count, last error |

For Frames, `state()["finished_count"]` is the number of stored frames; after a successful Integral acquisition, it is set to the requested `count`. Do not confuse it with `state()["frame_count"]`. Thread-safety of stopping from another thread requires hardware testing.

## Output and exceptions

Save formats are `NONE`, `TIFF`, `HDF5`, and `PIXET_NATIVE` (case-normalized); `"PIXET NATIVE"` is also accepted. TIFF writes individual `frame_000001.tiff` files. HDF5 appends to the `frames` dataset and flushes. Integral stores only the final image. PIXet-native output delegates to the SDK using `PX_FTYPE_AUTODETECT`; this class does not specify its internal format.

Invalid save formats or missing save paths raise `ValueError`; an unconnected device raises `RuntimeError`; SDK acquisition failures normally raise `RuntimeError`. Callback exceptions may propagate.

Source: supplied `pixet_ctrl.py` (unchanged).

For result data structures and timing, see [Measurement result data](../manual/frame_data.md).
