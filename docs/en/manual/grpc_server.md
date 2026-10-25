# gRPC server and local detector control

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/grpc_server.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/grpc_server.html">日本語</a>

## Verified implementation boundary

`MiniPixCtrl` is implemented in `pixet_ctrl.py` and provides local connection, configuration, acquisition, cancellation, frame access, and status APIs. **Only `pixet_ctrl.py` was examined here**; the existence or absence of gRPC components elsewhere in the project cannot be established.

## Intended architecture (not verified as implemented)

```text
Remote client → gRPC server → MiniPixCtrl → pypixet / PIXet → MiniPIX D08-W0313
```

Names found in earlier documentation—`pixet_grpc_server.py`, `SyncPixetGrpcClient`, and `AsyncPixetGrpcClient`—are retained as **proposed components or components that may exist in other source files**. Their classes, RPC methods, ports, and runnable examples have not been verified from the supplied source.

## Candidate remote interface based on verified local APIs

| Purpose | Verified `MiniPixCtrl` methods | gRPC exposure |
|---|---|---|
| Connection | `connect()` / `disconnect()` | Not verified |
| Configuration | `set_mode_all()` / `set_threshold()` / `set_clock()` / `set_bias()` | Not verified |
| Acquisition | `acquire()` / `acquire_frames()` / `acquire_integral()` | Not verified |
| Abort and state | `stop()` / `is_running()` / `is_aborting()` / `state()` | Not verified |
| Frames | `get_frame()` / `get_frames()` / `get_acq_frames()` | Not verified |

Frame data uses NumPy arrays. Any gRPC implementation must define shape, dtype, byte order, message limits, exclusive device access, and disconnect behavior. **These are design requirements, not features implicitly provided by `MiniPixCtrl`.**

## Transparent gRPC frame and API mapping

`grpc_frame` is a transparent transport frame for local control; it **does not add detector-control operations**. Remote control is therefore bounded by the operations implemented by the local controller on the server. Whether RPC/client names and signatures exactly match local methods requires the corresponding source code.


Do not interpret older RPC names as independent control features. If an operation is absent from local control, the transparent gRPC frame cannot supply it. Transport implementation and exposed RPC names cannot be verified from `pixet_ctrl.py` alone.
