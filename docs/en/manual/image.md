# Image data and file formats

<a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/image.html">日本語</a>

`_frame_to_dict()` copies PIXet `data()` into a NumPy array and reshapes it to `(height, width)`. Each frame dictionary includes `name`, `width`, `height`, `data`, `minimum`, `maximum`, `nonzero`, and `subframes`. Available subframes are read separately into `subframes`.

Supported save formats are `None`, `TIFF`, `HDF5`, and `PIXET_NATIVE`. TIFF writes one file per frame without conversion to display-oriented 8-bit values. HDF5 appends and flushes each completed frame in Frames mode, while Integral mode saves only the final integrated frame. PIXET_NATIVE delegates file writing to PIXet.

**Interpreting values:** Counting pixels represent threshold-crossing events; ToT/Energy values relate to time over threshold; Time/ToA values relate to arrival time. **Do not interpret raw ToT pixel values as keV without the relevant per-device calibration.** Integral frames must also be interpreted in the context of the configured mode and calibration.

Sources: supplied `pixet_ctrl.py`; MiniPIX Datasheet p. 5; PIXet Pro User's Manual pp. 8–9.
