# Python API overview and implementation status

<a href="https://ohara-lab-su.github.io/mini_pix/en/function/index.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/function/index.html">日本語</a>

This page distinguishes APIs defined in the supplied `pixet_ctrl.py` from potential future extensions. The actual detector is **MiniPIX D08-W0313** (Timepix, 500 µm silicon sensor). Use the device-specific calibration certificate for calibration settings; generic MiniPIX datasheet values are not a substitute.

## Implemented: `MiniPixCtrl`

The following methods are defined in the supplied `pixet_ctrl.py`. **Presence in source code does not imply exhaustive hardware testing.**

| Purpose | Methods |
| --- | --- |
| Initialization and connection | `__init__(logger, log_level=None)`, `connect()`, `disconnect()` |
| Detector configuration | `set_mode_all(mode)`, `set_threshold(...)`, `set_clock(...)`, `set_bias(...)` |
| Frame dimensions | `get_frame_size()` |
| Frame access and storage | `clear_frames()`, `get_frame_count()`, `get_frame(...)`, `get_frames(...)`, `get_current_frame()` |
| Acquisition-side frame access | `get_acq_frame_count()`, `get_acq_frames(...)` |
| Acquisition | `acquire(...)`, `acquire_frames(...)`, `acquire_integral(...)` |
| Abort and status | `stop()`, `is_running()`, `is_aborting()`, `state()` |

A `logger` argument is required. `set_mode_all()` accepts `"Counting"`, `"Energy"`, or `"Time"`. `connect()` selects the first detected device and does not automatically verify that its serial number belongs to D08-W0313. For parameters, return values, and storage behavior, see the <a href="https://ohara-lab-su.github.io/mini_pix/en/manual/ctrl_api.html">control API manual</a> and <a href="https://ohara-lab-su.github.io/mini_pix/en/tutorials/python_api.html">Python API tutorial</a>.

## Not implemented or not verified in supplied source

| Name | Status | Notes |
| --- | --- | --- |
| `SyncPixetGrpcClient` | Not verified in supplied source | Proposed synchronous gRPC client. |
| `AsyncPixetGrpcClient` | Not verified in supplied source | Proposed asynchronous gRPC client. |
| `pixet_grpc_server.py` | Not verified in supplied source | Proposed server component. |
| DeviceProxy | Not verified in supplied source | Proposed client-side abstraction. |

These designs are retained for potential future implementation. **They must not be treated as verified importable APIs.**

## Generated API reference

The <a href="https://ohara-lab-su.github.io/mini_pix/en/api/index.html">API Reference</a> is generated from the package source. Building it requires the repository's `src/mini_pix` directory.
