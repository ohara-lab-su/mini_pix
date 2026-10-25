# Implementation status and API scope

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/implementation_status.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/implementation_status.html">日本語</a>

This is the manual for the **`mini_pix` Python library**, not a replacement for the detector manufacturer's operating manual. The actual detector is **MiniPIX D08-W0313** (Timepix, 500 µm Si sensor, readout serial 2746). Values in its calibration certificate describe that particular unit under the recorded test conditions; they are not guarantees for other units or future measurements.

## APIs confirmed in the current implementation

The following methods are defined by `MiniPixCtrl` in the supplied `pixet_ctrl.py`. Presence in source code must not be confused with exhaustive hardware validation.

| Area | Implemented methods | Important distinction |
| --- | --- | --- |
| Connection | `connect()`, `disconnect()` | `connect()` does not verify the D08-W0313 unit identifier. |
| Configuration | `set_mode_all()`, `set_threshold()`, `set_clock()`, `set_bias()` | Modes are `Counting`, `Energy`, and `Time`; threshold input is in keV. |
| Acquisition | `acquire()`, `acquire_frames()`, `acquire_integral()` | Frames and integral acquisition differ; the PIXet SDK performs integral acquisition. |
| History | `clear_frames()`, `get_frame_count()`, `get_frame()`, `get_frames()`, `get_current_frame()` | These access the Python-side history. |
| SDK frames | `get_acq_frame_count()`, `get_acq_frames()` | Do not confuse SDK acquisition frames with Python history. |
| State | `stop()`, `is_running()`, `is_aborting()`, `state()` | Stop latency and thread behavior are not guaranteed under every condition. |

`MiniPixCtrl` requires a `logger` constructor argument. The `acquire()` `save_format` accepts `None`, `TIFF`, `HDF5`, or `PIXET_NATIVE`. The interpretation of `save_path` depends on the selected format; see the acquisition and storage documentation.

## Unimplemented or unverified functionality

The supported acquisition API consists of `acquire()`, `acquire_frames()`, and `acquire_integral()`.

Descriptions of `grpc_server` and `DeviceProxy` are retained as **future design or implementation unverified**. The supplied `pixet_ctrl.py` alone does not establish a gRPC server, proxy implementation, or concrete RPC method names. These should not be presented as implemented `MiniPixCtrl` methods.

## Relationship between calibration and the Python API

The D08-W0313 calibration certificate reports a threshold DAC value of approximately THL 691 for 5 keV and bias-test results under factory test conditions. The argument to `set_threshold(threshold_kev)` is **energy in keV**, not the raw THL DAC value. Factory test values are not Python defaults.

The manufacturer's PDFs are primary references for detector handling, product characteristics, and calibration. The supplied `pixet_ctrl.py` is the source of truth for the Python API. An operation described in the manufacturer's manual is not necessarily exposed by the Python wrapper.
