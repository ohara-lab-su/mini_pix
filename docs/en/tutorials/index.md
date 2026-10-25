# MiniPIX / PIXet Control Documentation

<a href="https://ohara-lab-su.github.io/mini_pix/en/tutorials/index.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/tutorials/index.html">日本語</a>

This documentation describes the MiniPIX control API based on `MiniPixCtrl` in `pixet_ctrl.py`.

`MiniPixCtrl` is a high-level wrapper that directly uses `pypixet`, the PIXet Pro Python API. Applications can perform connection management, detector configuration, exposure, and frame acquisition through Python methods without directly manipulating low-level PIXet SDK objects.

```{toctree}
:maxdepth: 1

quick_start
architecture
python_api
grpc_intro
grpc
```

The current implementation covers:

- Starting and shutting down the PIXet core.
- Connecting to the first detector.
- Detecting `FileDevice 0` and treating the absence of a physical detector as a connection failure.
- Setting the acquisition mode for all pixels.
- Configuring the threshold, Timepix clock, and bias voltage.
- Acquiring ordinary frames through `doSimpleAcquisition()`.
- Converting frames retained in PIXet's internal memory into Python dictionaries.

Methods that have not yet been implemented are identified in the API documentation.
