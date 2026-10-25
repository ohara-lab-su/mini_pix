# DeviceProxy integration

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/device_proxy.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/device_proxy.html">日本語</a>

## Purpose and evidence

Earlier documentation describes DeviceProxy as an **architectural abstraction** intended to expose local and remote devices through a common application interface. That design is retained. However, the supplied `pixet_ctrl.py` does not define DeviceProxy; its constructors, registration functions, and transport implementation cannot be verified here.

## Intended responsibilities

- Local: `MiniPixCtrl` controls PIXet and the detector (**verified**).
- Remote: a gRPC client delegates calls to a server (**not verified from the supplied source**).
- Proxy: the application uses a uniform interface regardless of transport (**design goal; implementation unverified**).

Previously documented names such as `register_device` and `DeviceProxy` are retained as **possible future or separate implementations**, not runnable examples. When their source is available, document the actual import paths, constructor signatures, and synchronous/asynchronous behavior.

## Interface compatibility

Candidate common methods include `connect()`, `disconnect()`, `set_mode_all()`, `set_threshold()`, `acquire_frames()`, `acquire_integral()`, `stop()`, and `state()`. **Only the local `MiniPixCtrl` implementation is verified**; remote compatibility is not yet established.

## Transparent gRPC frame and API mapping

`grpc_frame` is a transparent transport frame for local control; it **does not add detector-control operations**. Remote control is therefore bounded by the operations implemented by the local controller on the server. Whether RPC/client names and signatures exactly match local methods requires the corresponding source code.


Do not interpret older RPC names as independent control features. If an operation is absent from local control, the transparent gRPC frame cannot supply it. Transport implementation and exposed RPC names cannot be verified from `pixet_ctrl.py` alone.
