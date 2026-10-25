# PIXet Python SDK and control

<a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/pixet_sdk.html">日本語</a>

`pixet_ctrl.py` is a local wrapper around `pypixet`, not a complete implementation of the PIXet Pro GUI. Initialization uses `pypixet.start()`, shutdown uses `pypixet.exit()`, and the connected device's `pixCfg()` is retained.

| Public method | Purpose |
|---|---|
| `connect()` / `disconnect()` | Open and close the device |
| `set_mode_all(mode)` | Map `Counting` / `Energy` / `Time` to PIXet constants |
| `set_threshold(threshold_kev)` | Set the energy threshold in keV |
| `set_clock(clock_mhz)` | Set the Timepix clock |
| `set_bias(bias_volt)` | Set sensor bias |
| `acquire_frames(count, sec, ...)` | Frame acquisition |
| `acquire_integral(count, sec, ...)` | PIXet-native integral acquisition |
| `stop()` / `state()` | Stop and inspect state |

`set_mode_all()` maps to `PX_TPXMODE_MEDIPIX`, `PX_TPXMODE_TOT`, and `PX_TPXMODE_TIMEPIX`. **Threshold is in keV, not a raw THL DAC code.** The clock and bias setters forward values to PIXet; the supplied implementation does not validate safe ranges. Choose values based on the specific unit's calibration and manufacturer specifications.

`set_bias()` checks the SDK return code but does not independently read back the actual bias or leakage current. Refer to the distributed PIXet SDK documentation for functionality beyond this wrapper.

Sources: supplied `pixet_ctrl.py`; PIXet Pro User's Manual pp. 8–9, 13.
