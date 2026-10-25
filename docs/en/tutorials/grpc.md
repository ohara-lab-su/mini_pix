# Python API over gRPC

<a href="https://ohara-lab-su.github.io/mini_pix/jp/tutorials/grpc.html">日本語</a>

`grpc_frame` transparently exposes local control methods; it does not introduce detector-specific operations. The authoritative detector API is `MiniPixCtrl`.

| Operation | Local Python API |
|---|---|
| Connection | `connect()` / `disconnect()` |
| Configuration | `set_mode_all()` / `set_threshold()` / `set_clock()` / `set_bias()` |
| Frame acquisition | `acquire_frames(count, sec, ...)` |
| Integral acquisition | `acquire_integral(count, sec, ...)` |
| Common acquisition | `acquire(count, sec, acquisition_type="frames", ...)` |
| Data access | `get_frame()` / `get_frames()` / `get_acq_frames()` |
| State and stop | `state()` / `stop()` / `is_running()` |

Both acquisition wrappers delegate to `acquire()`. The returned dictionary includes `frames`, `frame_count`, and `saved_file`. Use `set_mode_all("Energy")` to select the ToT mode.

The server and client implementation sources were not provided, so this page does not present unverified connection code or client class names as executable examples.
