# gRPC integration: design and implementation status

<a href="https://ohara-lab-su.github.io/mini_pix/en/tutorials/grpc_intro.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/tutorials/grpc_intro.html">日本語</a>

## Intended use

The design places `MiniPixCtrl` on the detector-connected computer with PIXet installed and allows applications on other computers to control it. The separation between local hardware access and network transport remains a valid design goal.

```text
Application → DeviceProxy (proposed; unverified)
            → gRPC client (unverified)
            → gRPC server (unverified)
            → MiniPixCtrl (verified in pixet_ctrl.py)
            → pypixet / PIXet → MiniPIX D08-W0313
```

## Verified local usage

```python
import logging
from mini_pix.pixet_ctrl import MiniPixCtrl

logger = logging.getLogger("mini_pix")
ctrl = MiniPixCtrl(logger=logger)
if not ctrl.connect():
    raise RuntimeError("Detector connection failed")
try:
    if not ctrl.set_mode_all("Energy"):
        raise RuntimeError("Mode configuration failed")
    result = ctrl.acquire_frames(count=1, sec=1.0)
finally:
    ctrl.disconnect()
```

This is a **local API example**, not a runnable gRPC client example. Set threshold and bias according to the experiment and detector calibration.

## Future extensions

The earlier design names `SyncPixetGrpcClient`, `AsyncPixetGrpcClient`, `pixet_grpc_server.py`, and DeviceProxy. These remain documented as design candidates; their implementation cannot be established from the supplied file. Avoid inventing import paths or endpoints. Frame serialization, concurrent access, and abort semantics require separate transport-level specifications.

## Transparent gRPC frame and API mapping

`grpc_frame` is a transparent transport frame for local control; it **does not add detector-control operations**. Remote control is therefore bounded by the operations implemented by the local controller on the server. Whether RPC/client names and signatures exactly match local methods requires the corresponding source code.


Do not interpret older RPC names as independent control features. If an operation is absent from local control, the transparent gRPC frame cannot supply it. Transport implementation and exposed RPC names cannot be verified from `pixet_ctrl.py` alone.
