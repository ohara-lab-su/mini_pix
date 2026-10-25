# Frame and integral acquisition

<a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/acquisition.html">日本語</a>

`MiniPixCtrl.acquire(count, sec, acquisition_type="frames", callback=None, save_format=None, save_path=None)` is the shared acquisition API. `count` is the number of measurements, and `sec` is the exposure duration in seconds per measurement. Only `frames` and `integral` are accepted.

**Frames:** Uses `doSimpleAcquisition()`. When a callback, TIFF saving, or HDF5 saving is requested, it registers `PX_EVENT_ACQ_FINISHED` and reads each completed frame. Otherwise it retrieves frames using `acqFrameCount()` and `acqFrame()` after the acquisition finishes. The resulting frames are retained in memory.

**Integral:** Uses `doSimpleIntegralAcquisition()`. **The Python controller does not sum the images itself.** It reads the final integral frame and invokes the callback once, if supplied. The number of returned images should not be assumed to match a frames acquisition with the same `count`.

The result dictionary contains `rc`, `acquisition_type`, `frame_count`, `frames`, and `saved_file`. Each frame includes image data, dimensions, and summary statistics. Errors raise exceptions and can be inspected through `state()`.

**Note:** `acquire()` is synchronous and does not return until the operation completes. Stopping it externally requires another execution context to call `stop()`. Device behavior and interruption latency have not been tested here.

Source: supplied `pixet_ctrl.py`, `acquire()`, `acquire_frames()`, and `acquire_integral()`.
