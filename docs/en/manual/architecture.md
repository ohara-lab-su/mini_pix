# mini_pix architecture and implementation boundaries

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/architecture.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/architecture.html">日本語</a>

## Implemented control path

```text
Python application → MiniPixCtrl → pypixet / PIXet core → MiniPIX D08-W0313
```

The supplied `pixet_ctrl.py` is a local PIXet SDK wrapper and does not itself perform gRPC communication. The D08-W0313 detector uses Timepix and a 500 µm silicon sensor; its device-specific calibration is documented by the manufacturer. `connect()` selects the first detected device and does not automatically select D08-W0313 by serial number.

## Proposed extension path (unverified)

```text
Application → DeviceProxy → gRPC client → gRPC server → MiniPixCtrl → PIXet
```

The gRPC and DeviceProxy layers described in earlier documentation are retained as an extensible architecture. Their implementation cannot be verified from the supplied source, so **implemented local APIs** are distinguished from **proposed or unverified upper layers**.

## Data and control

`acquire_frames()` delegates frame acquisition to PIXet, while `acquire_integral()` uses PIXet integral acquisition. Results contain Python dictionaries and NumPy arrays. Local HDF5/TIFF saving is supported; network transport and remote access arbitration are outside this class's responsibility.

Any future gRPC layer should preserve local API units for detector modes, thresholds, and bias, and define a compatible representation of measurement results. See [gRPC server](grpc_server.md) and [DeviceProxy](device_proxy.md).

## Transparent gRPC frame and API mapping

`grpc_frame` is a transparent transport frame for local control; it **does not add detector-control operations**. Remote control is therefore bounded by the operations implemented by the local controller on the server. Whether RPC/client names and signatures exactly match local methods requires the corresponding source code.


Do not interpret older RPC names as independent control features. If an operation is absent from local control, the transparent gRPC frame cannot supply it. Transport implementation and exposed RPC names cannot be verified from `pixet_ctrl.py` alone.
