# Architecture

<a href="https://ohara-lab-su.github.io/mini_pix/en/tutorials/architecture.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/tutorials/architecture.html">日本語</a>

## Basic structure

The central component of `pixet_ctrl.py` is `MiniPixCtrl`.

```text
User Application
    │
    ▼
MiniPixCtrl
    │
    ▼
pypixet / PIXet Python API
    │
    ▼
PIXet core
    │
    ▼
MiniPIX / Timepix detector
```

`MiniPixCtrl` is a high-level control layer that provides a thin wrapper around the PIXet Pro Python API. It brings together connection management, pixel configuration, detector parameter settings, exposure, and frame retrieval.

## Internal state

`MiniPixCtrl` primarily maintains the following internal references:

- `_pixet`: Main PIXet core object obtained from `pypixet.pixet`.
- `_dev`: Detector object obtained from `pixet.devices()`; currently the first device is used.
- `_pixcfg`: Pixel configuration obtained from `_dev.pixCfg()`.
- `_logger`: A supplied logger or the standard `logging` logger.

## Initialization on connection

For Timepix / MPX2 devices, the pixel mode is configured through the pixel configuration rather than through `setOperationMode()`. Currently, `connect()` sets every pixel to `PX_TPXMODE_TOT` immediately after connecting and applies the configuration to the device using `setToDevice()`.

Accordingly, measurement modes are changed through `set_mode_all()`.

## Frame acquisition structure

Image acquisition is delegated to PIXet's `doSimpleAcquisition()`. After acquisition, frames stored within the PIXet core are retrieved with `acqFrameRefInc()` and converted to Python dictionaries by `_frame_to_dict()`.

```text
doSimpleAcquisition()
    │
    ▼
PIXet internal acquisition frames
    │
    ▼
acqFrameRefInc(idx)
    │
    ▼
_frame_to_dict(frame)
    │
    ▼
{"name", "width", "height", "data", "subframes"}
```

`_frame_to_dict()` reads not only the main frame but also `subFrames()` when available. Each retrieved frame and subframe is ultimately released using `destroy()`.

## Role in a gRPC deployment

For network access, `MiniPixCtrl` runs on the server, and gRPC clients call equivalent control methods.

```text
Client Program
    │
    ▼
SyncPixetGrpcClient / AsyncPixetGrpcClient
    │
    ▼
gRPC
    │
    ▼
pixet_grpc_server.py
    │
    ▼
MiniPixCtrl
    │
    ▼
PIXet Python API
    │
    ▼
MiniPIX Detector
```

Direct detector control remains inside the server process connected to the physical hardware; users interact through the client API.
