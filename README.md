# mini_pix

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/mini_pix/blob/main/README.en.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/mini_pix/blob/main/README.md)

A Python package for controlling ADVACAM MiniPIX / Timepix through the PIXet Python API, both locally and remotely using `grpc_frame`.

Version 0.1.0 is the first baseline release verified with a MiniPIX connected to a server and a client running on a separate machine. The following operations were tested:

- Frames acquisition
- Integral acquisition
- Remote VIEW
- Client-side TIFF / PNG saving

## Architecture

`mini_pix` separates the local detector-control layer from the remote-control layer over gRPC.

```text
Client
  |
  | grpc_frame / gRPC
  v
MiniPIX Server
  |
  v
MiniPixCtrl
  |
  v
PIXet Python API (pypixet)
  |
  v
MiniPIX / Timepix
```

The server requires the PIXet Python API and a physical MiniPIX detector.

The client does not require the PIXet Python API or `pypixet`. When importing the client API, `mini_pix.server_grpc` does not load the server implementation. It imports that implementation lazily only when `pixet_grpc_server` or `pixet_server` is needed.

## Development history leading to v0.1.0

Version 0.1.0 is not simply an extension of the earlier v0.0.x series.

By v0.0.4, DeviceProxy, Frames, Integral, and the gRPC client had been implemented, and development was proceeding toward an anticipated v0.0.5 release. However, some of the earlier tests had been performed without X-ray irradiation. Consequently, successful communication and API calls had not been sufficiently distinguished from acquisition of physically correct detector images.

Subsequent measurements under X-ray irradiation, comparing images from the PIXet Pro GUI with those from the Python API, revealed that the Python implementation did not reproduce the behavior of the official GUI. Rather than layering fixes onto the old implementation, development returned to minimal local code using the PIXet Python API and progressively rebuilt physical detector control.

The redesign proceeded in this order: baseline verification with the PIXet Pro GUI; minimal API code; calibration / device configuration; raw frames; GUI display; multiple frames; class-based implementation; callbacks; saving; Integral acquisition; integration into `MiniPixCtrl`; and finally gRPC / remote VIEW. The resulting implementation became v0.1.0 and serves as the baseline for subsequent releases.

### Local validation code used during the redesign

- `01a.py`: Verified PIXet core startup, physical-device detection, mode / threshold settings, and basic `doSimpleAcquisition()` behavior in a minimal configuration.
- `01b_tiff.py`: Matched the GUI baseline conditions, obtained `frame.data()` directly with `PX_FTYPE_NONE`, and saved raw TIFF files. This distinguished SDK image output from raw detector data.
- `01b_gui_memory.py`: Displayed memory frames directly. Separated raw data from display processing and verified vertical orientation matching the PIXet GUI, Auto / Manual range, and Nearest / Smooth rendering.
- `01c_gui_memory.py`: Separated device initialization, configuration, and single-frame acquisition into functions independent of the GUI.
- `01d_gui_function.py`: Organized batch acquisition of multiple frames and retrieval of all frames after acquisition into functions.
- `01e_gui_class.py`: Encapsulated PIXet / MiniPIX initialization, configuration, acquisition, and shutdown in a GUI-independent class, separating control and display layers.
- `01f_gui_callback.py`: Used `PX_EVENT_ACQ_FINISHED` to retrieve each frame via callback during Frames acquisition, while retaining post-acquisition retrieval without callbacks.
- `01g_gui_save_intAcq.py`: Added TIFF / HDF5 / PIXet native saving, Stop / state, and Integral acquisition. Established use of `doSimpleIntegralAcquisition()` for Integral acquisition rather than summing frames in Python.

These files are not an independent implementation; they document the physical-device validation and redesign process that led to the current `pixet_ctrl.py`, `view_local.py`, and `view_client.py`.

## Main modules

### `mini_pix.pixet_ctrl.MiniPixCtrl`

The local control class for MiniPIX / Timepix.

It uses the PIXet Python API directly and does not handle gRPC, GUI, or server/client configuration.

Main methods:

- `connect()` / `disconnect()`
- `set_mode_all()`
- `set_threshold()`
- `set_clock()`
- `set_bias()`
- `acquire()`
- `acquire_frames()`
- `acquire_integral()`
- `stop()`
- `is_running()`
- `is_aborting()`
- `state()`
- `clear_frames()`
- `get_frame_count()`
- `get_frame()`
- `get_frames()`
- `get_current_frame()`
- `get_acq_frame_count()`
- `get_acq_frames()`

The `logger` argument is required for `MiniPixCtrl`.

### Frames acquisition

Standard frame acquisition:

```python
result = ctrl.acquire_frames(
    count,
    sec,
)
```

When PIXet acquisition events are available, the latest frame is retrieved and passed to the callback for each `PX_EVENT_ACQ_FINISHED` event.

### Integral acquisition

```python
result = ctrl.acquire_integral(
    count,
    sec,
)
```

Integral acquisition uses PIXet's `doSimpleIntegralAcquisition()`. It does not generate an integral image by summing Frames images in Python.

Even when a callback is specified, Integral acquisition invokes it only once, for the final integrated frame.

## Frame data

Acquired frames are represented as dictionaries with the following main entries:

```text
name
width
height
data
minimum
maximum
nonzero
subframes
```

`data` is a two-dimensional NumPy array.

The array obtained from the detector is retained as raw data for saving, separately from any transformations used for display.

## Saving

`MiniPixCtrl.acquire()`, `acquire_frames()`, and `acquire_integral()` support the following server-side save formats:

```text
NONE
TIFF
HDF5
PIXET_NATIVE
```

### TIFF

Each frame is saved as a separate TIFF file.

The acquired numerical array is saved directly with `tifffile`, without display normalization or other visualization processing.

### HDF5

For Frames acquisition, each frame is appended to a dataset, followed by an immediate `flush()`.

For Integral acquisition, the final integrated frame is saved.

The dataset uses the dtype of the acquired NumPy array.

### PIXET_NATIVE

Uses PIXet's own file-saving functionality.

## gRPC

### Server

`mini_pix.server_grpc.pixet_grpc_server()` creates `MiniPixCtrl` and exposes it through `grpc_frame.grpc_server.create_grpc_server()`.

Ordinary control APIs are exposed as unary RPCs.

Incremental image transfer for Frames / Integral acquisition uses `grpc_frame`'s `StreamCall`.

A server startup example is provided in `example/start_minipix_server.py`.

```python
from mini_pix.config import Config
from mini_pix.server_grpc import pixet_grpc_server
from x_logger import XLogger

config = Config("mini_pix.yaml")

logger = XLogger(
    log_level=config.LOGGER_LEVEL,
    logger_name=config.SERVER_LOGGER_NAME,
)

pixet_grpc_server(
    grpc_host=config.SERVER_IP,
    grpc_port=config.SERVER_PORT,
    auto_connect=True,
    logger=logger,
    log_level=config.LOGGER_LEVEL,
)
```

### DeviceProxy

`mini_pix.server_grpc` registers the MiniPIX client with `grpc_frame.DeviceProxy`.

Default name:

```text
mini_pix
```

Aliases:

```text
pixet
MiniPix
MiniPixCtrl
pixet_grpc
```

Synchronous client example:

```python
from mini_pix.server_grpc import DeviceProxy

client = DeviceProxy(
    "mini_pix",
    server_ip="10.170.10.38",
    server_port=50051,
    set_timeout_sec=30.0,
    async_mode=False,
)
```

`async_mode=False` uses `SyncPixetGrpcClient`; `async_mode=True` uses `AsyncPixetGrpcClient`.

### Client-side save

`acquire_frames()` and `acquire_integral()` in `SyncPixetGrpcClient` / `AsyncPixetGrpcClient` support client-side saving.

```python
client.acquire_frames(
    1,
    1.0,
    name="frame.tiff",
    save_local=True,
    return_data=False,
)
```

Supported client-side file extensions:

- `.tif`
- `.tiff`
- `.png`

TIFF files preserve the raw numerical array.

PNG files are intended for display: each frame is min-max normalized and saved as a 16-bit grayscale PNG.

## VIEW

### `example/view_local.py`

A local VIEW that directly uses `MiniPixCtrl`.

It does not use gRPC and receives frames through `MiniPixCtrl` callbacks.

### `example/view_client.py`

A VIEW for use from a separate machine over gRPC.

- Switch between Frames and Integral acquisition
- Configure count / acquisition time
- Configure detector mode / threshold / bias / clock
- Receive frames through `StreamCall`
- Maintain a local history of received frames
- Browse history using a slider and previous/next buttons
- Auto / Manual display range
- Nearest / Smooth rendering
- Stop

The client VIEW does not require `pypixet`.

## Examples

### `measure_simple.py`

Synchronous client example for Frames acquisition.

Current sample settings:

```text
Mode      : Counting
Threshold : 5.0 keV
Bias      : 150 V
Clock     : 9.66667 MHz
Count     : 1
Time      : 1.0 s
```

TIFF saving is enabled; the PNG saving example remains commented out.

### `measure_integral.py`

Synchronous client example for Integral acquisition.

Current sample settings:

```text
Mode      : Counting
Threshold : 5.0 keV
Bias      : 150 V
Clock     : 9.66667 MHz
Count     : 1
Time      : 10.0 s
```

TIFF saving is enabled; the PNG saving example remains commented out.

### `start_minipix_server.py`

Reads `mini_pix.yaml` and starts the MiniPIX gRPC server.

## Configuration file

Current entries in `example/mini_pix.yaml`:

```yaml
SERVER_IP: "10.170.10.38"
SERVER_PORT: 50051
CLIENT_LOGGER_NAME: "mini_pix_client"
SERVER_LOGGER_NAME: "mini_pix_server"
TIMEOUT: 30.0
LOGGER_LEVEL: "debug"
ASYNC_MODE: false
```

Change the IP address and other settings to match your environment.

## Configuration verified with v0.1.0

In v0.1.0, operation was verified between a server connected to MiniPIX / PIXet and a client on a separate machine using:

- `view_client.py`
- `measure_simple.py`
- `measure_integral.py`

These are the baseline verified operations for v0.1.0.

------------------------------------------------------------------------

## PIXet / pypixet setup

## Calibration / device configuration

For MiniPIX, successfully importing the Python API and detecting the physical device is not sufficient. Correct loading of the device configuration / calibration XML corresponding to the specific detector is essential.

The device used here was:

```text
Device : MiniPIX D08-W0313
Serial : 2746
Chip   : Timepix
Sensor : Si, 500 µm
```

### Problem identified through X-ray measurements

The official PIXet Pro GUI produced correct images under these conditions:

```text
Mode      : Counting
Threshold : 2.4 keV
Bias      : 150 V
Clock     : 9.66667 MHz
Time      : 1 s
```

Initial minimal Python API code operating the same device did not reproduce the GUI's image behavior under actual X-ray irradiation. Matching mode, threshold, bias, and clock values alone did not resolve the discrepancy. Loading the device-specific XML proved to be a critical difference.

### Calibration XML supplied on USB

The supplied USB drive contains the device-specific file:

```text
Calibration/MiniPIX-D08-W0313.xml
```

For the API environment, place it in the `factory` directory of the PIXet API installation:

```text
C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64
└─ factory
   └─ MiniPIX-D08-W0313.xml
```

After placing this file, the images acquired through the Python API behaved almost identically to those from the official GUI.

Therefore, the v0.1.0 server setup includes not only Python 3.7, DLLs, and `pixet.ini`, but also installation of the XML corresponding to the specific MiniPIX detector.

### `factory` and `configs`

PIXet core preferentially loads saved configurations from `configs`; if no usable configuration exists, it uses the device's initial settings from `factory`. The `configs` directory is created or updated during shutdown and its contents are used as the current configuration at the next startup.

Thus, the device-specific calibration XML in `factory` and the XML saved by PIXet into `configs` after execution have different roles. Actual differences in entries and values were also observed between XML used or saved by the official GUI and XML generated on the Python API side; these must not be treated as interchangeable files.

This issue is more than an installation caveat: it directly motivated the redesign from v0.0.x to v0.1.0. Going forward, successful API calls, communication, or image-file generation alone are not considered proof of correct detector control. The standard for physical-device verification is to compare X-ray images against the official GUI using the same detector and measurement conditions.

The following sections describe setup on the server directly connected to MiniPIX.

### PIXet installation

### Downloads

- [Advacam Downloads](https://advacam.com/downloads/)
- Alternatively, use the supplied USB drive.

### Installing drivers and related software

- Serial driver: Run the installer under the USB drive's `Drivers` directory (with the detector disconnected).
- GUI and drivers: Run the installer under `Pixet/Pixet_pro_windows` on the USB drive.
- Restart the computer.

### Prerequisites for the Python API

- [Microsoft Visual C++ Redistributable 2015–2022 (x64)](https://learn.microsoft.com/ja-jp/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-c-v14-redistributable)

### Installing the Python API

- Python 3.7 is required ([pyenv-win](https://qiita.com/probabilityhill/items/9a22f395a1e93206c846) is recommended for installation).
- See [Installing the Python API and related notes](#installing-the-python-api-and-related-notes).
- Prepare `C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64`.

## AdvaCam documentation

- [PIXet](https://wiki.advacam.cz/wiki/PIXet)
- [Pixet SDK](https://wiki.advacam.cz/wiki/Pixet_SDK)
- [Pixet Python API](https://wiki.advacam.cz/wiki/Python_API)

------------------------------------------------------------------------

## Installing the Python API and related notes

- PIXet information for Python:
- <https://wiki.advacam.cz/wiki/Pixet_SDK>
- <https://wiki.advacam.cz/wiki/Python_API>

Documentation PDFs are included in the API ZIP archive located in the PIXet folder.

Extract the ZIP archive from the PIXet folder on the supplied USB drive. There is no `pip` installer or `setup.py`; therefore, either run Python programs in the directory containing the extracted module files or make that directory importable using `site.addsitedir(pixet_dir)`, as described below.

### Main module files

- `pypixet.pyd`: Main API for basic device operations, including configuration, acquisition, and status retrieval.
- `pypxproc.pyd`: Pixel processing, used by clustering and spectral-imaging objects.

### Log directory

The `logs` subdirectory under the directory from which the program is executed.

### Other files required to use the modules

- `pixet.ini`: Place in the same directory as the program.

```ini
[Settings]
Splash=false

[Hwlibs]
fitpix.dll
minipix.dll
widepix.dll
zem.dll
zest.dll
```

### Dependencies

DLLs required by `xcore.dll`:

```text
mfc110.dll
mfcloop.dll
msvcp120.dll
msvcp140.dll
msvcr110.dll
msvcr120.dll
vccorlib140.dll
vcruntime140.dll
```

## Troubleshooting the PIXet installation

### Main files on the supplied USB drive

- `PIXet_Pro_1.8.3_Windows_x86_64`: GUI application (for regular users).
- `API_PIXet_Pro_1.8.3_Windows_x86_64`: Developer package containing the SDK for control from Python / C / C++.

Running Python from the extracted `API_PIXet_Pro` directory (there are several ways to run it, described below) initially fails because the following runtime DLLs are missing:

```text
VCRUNTIME140.dll
VCRUNTIME140_1.dll
MSVCP140.dll
```

Install [Microsoft Visual C++ Redistributable 2015–2022 (x64)](https://learn.microsoft.com/ja-jp/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-c-v14-redistributable).

However, installing the standard runtime alone is still insufficient. Next, inspect the dependencies of the `.pyd` file underlying the `pypixet` module.

```python
import pefile

# Inspect DLL dependencies of the .pyd file.
pe = pefile.PE(r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64\pypixet.pyd")

for entry in pe.DIRECTORY_ENTRY_IMPORT:
    print(entry.dll.decode())
```

The result is:

```text
PS C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64> python .\b.py
python37.dll
MSVCP140.dll
WSOCK32.dll
WS2_32.dll
KERNEL32.dll
VCRUNTIME140.dll
VCRUNTIME140_1.dll
api-ms-win-crt-runtime-l1-1-0.dll
api-ms-win-crt-stdio-l1-1-0.dll
api-ms-win-crt-filesystem-l1-1-0.dll
api-ms-win-crt-time-l1-1-0.dll
api-ms-win-crt-heap-l1-1-0.dll
api-ms-win-crt-string-l1-1-0.dll
PS C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64>
```

This shows that `pypixet` was built for Python 3.7. Python 3.7 must therefore be installed to use this particular module build.

    pyenv install 3.7.9

Because `os.add_dll_directory()` is unavailable in Python 3.7.9, modify `PATH` instead:

```python
# Python <= 3.7
import os
import site

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

# Python 3.7 has no add_dll_directory(); modify PATH instead.
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)  # Make .pyd files importable.
import pypixet

print("OK")
```

This allows a Git project located elsewhere to use the module.

## Scripts for checking Python version compatibility with a .pyd file

### Python >= 3.8

```python
# Check whether a .pyd in a specified directory can be loaded from elsewhere.
# The Python version must match the version required by the .pyd file.

# Python >= 3.8
import os
import ctypes

dll_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
os.add_dll_directory(dll_dir)
ctypes.WinDLL(r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64\pypixet.pyd")
print("OK")
```

### Python <= 3.7

```python
# Check whether a .pyd in a specified directory can be loaded from elsewhere.
# The Python version must match the version required by the .pyd file.

# Python <= 3.7
import os
import ctypes

dll_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
os.environ["PATH"] = dll_dir + ";" + os.environ["PATH"]
ctypes.WinDLL(os.path.join(dll_dir, "pypixet.pyd"))
print("OK")
```

------------------------------------------------------------------------

## Using modules installed in an arbitrary directory (summary)

### Python >= 3.8

```python
# Works even when the module directory is located elsewhere.
# Python >= 3.8
import os

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
os.add_dll_directory(pixet_dir)
import site

site.addsitedir(pixet_dir)
import pypixet

print("OK")
```

### Python <= 3.7

```python
# Works even when the module directory is located elsewhere.

# Python <= 3.7
import os
import site

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

# Python 3.7 has no add_dll_directory(); modify PATH instead.
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)  # Make .pyd files importable.
import pypixet

print("OK")
```

### Installing modules from the PIXet 2026.03 supplied USB drive (module3)

- Install Python **3.7**.
- Install [Microsoft Visual C++ Redistributable 2015–2022 (x64)](https://learn.microsoft.com/ja-jp/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-c-v14-redistributable).

Use `pypixet` as follows:

```python
import os
import site

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)  # Make .pyd files importable.

import pypixet
```
