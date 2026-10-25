# Quick start — Python control

<a href="https://ohara-lab-su.github.io/mini_pix/en/tutorials/quick_start.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/tutorials/quick_start.html">日本語</a>

## Scope and prerequisites

This guide documents the **Python control layer** of `mini_pix`; it does not replace the detector manufacturer's manual. The actual detector is **MiniPIX D08-W0313** (Timepix, 500 µm silicon sensor, readout serial 2746). The reference sources are its individual calibration record and the supplied `pixet_ctrl.py`.

The supplied code hard-codes the Windows PIXet API path `C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64`. Installing PIXet Pro and setting up the `pypixet` Python SDK are separate concerns. The code also imports `h5py`, `numpy`, and `tifffile`. Confirm Python compatibility against the SDK distribution in use.

## Acquisition example

This example uses only methods present in the supplied source. A `logger` is required. Mode and threshold are configured explicitly. **Bias is deliberately not set here**: the appropriate voltage depends on the experimental setup and safety procedure.

```python
import logging
from mini_pix.pixet_ctrl import MiniPixCtrl

logger = logging.getLogger("mini_pix")
logging.basicConfig(level=logging.INFO)
pix = MiniPixCtrl(logger=logger)

if not pix.connect():
    raise RuntimeError("Physical MiniPIX detector not found")

try:
    if not pix.set_mode_all("Counting"):
        raise RuntimeError("Mode configuration failed")
    if not pix.set_threshold(5.0):
        raise RuntimeError("Threshold configuration failed")

    result = pix.acquire_frames(count=2, sec=0.5)
    print(result["frame_count"])
    print(result["frames"][0]["data"].shape)
finally:
    pix.disconnect()
```

`connect()` selects the first detected device and rejects `FileDevice 0`, but **does not verify the D08-W0313 identity**. Check the logged serial number. It does not automatically enable ToT mode.

## Modes and saving

`set_mode_all()` accepts only `"Counting"`, `"Energy"`, or `"Time"`. `set_threshold(5.0)` accepts an energy in **keV**, not the raw calibration DAC setting `THL=691`.

`acquire_frames()` returns individual frames; `acquire_integral()` returns the PIXet-integrated result without summing in Python, invoking the callback once on completion. Supported save formats are `None`, `"TIFF"`, `"HDF5"`, and `"PIXET_NATIVE"`. For TIFF, `save_path` is a directory; for HDF5 and native output, it is a filename. The HDF5 dataset is `frames`.

## References

- [Python API](python_api.md)
- [Acquisition modes](../manual/acquisition.md)
- [Device calibration](../manual/calibration.md)

Manufacturer references: D08-W0313 Calibration protocol, MiniPIX Datasheet, PIXet Pro User's Manual.