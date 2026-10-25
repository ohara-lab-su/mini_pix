# Measurement results: data structure and acquisition timing

<a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/frame_data.html">日本語</a> | <a href="https://ohara-lab-su.github.io/mini_pix/en/manual/frame_data.html">English</a>

This page specifies the **Python data** returned by `MiniPixCtrl`, rather than the detector calibration procedure or PIXet Pro user interface. It is based on `_frame_to_dict()`, `_store_frame()`, `acquire()`, and `get_acq_frames()` in the current `pixet_ctrl.py`.

## Acquisition result

`acquire()`, `acquire_frames()`, and `acquire_integral()` return a dictionary with these keys:

| Key | Meaning |
| --- | --- |
| `rc` | Integer return code from the PIXet SDK acquisition call. |
| `acquisition_type` | `"frames"` or `"integral"`. |
| `frame_count` | Number of result frames stored in Python; not necessarily equal to requested `count`. |
| `frames` | List of frame dictionaries. |
| `saved_file` | Save destination: empty string without saving, directory for TIFF, file path for HDF5, or requested filename for PIXet native. |

Each frame contains `name`, `width`, `height`, `data`, `minimum`, `maximum`, `nonzero`, and `subframes`. `data` is a **NumPy array**, with `shape == (height, width)`, copied from the SDK before reshaping. `minimum` and `maximum` are the array extrema; `nonzero` counts nonzero pixels. When available, `subframes` contains dictionaries with `name`, `width`, `height`, and `data`. Do not assume that these raw arrays are calibrated energy spectra or event lists.

## SDK acquisition frames versus Python history

`get_frame_count()`, `get_frame()`, `get_frames()`, and `get_current_frame()` access **Python-managed history**. `get_acq_frame_count()` and `get_acq_frames(idx=None)` access **PIXet SDK acquisition data**. The latter returns a dictionary of the form `{"frame_count": integer, "frames": list}`, not a bare list. When `idx` is specified, it reads that frame and reports `frame_count` as 1. The API does not require the SDK and Python history counts to agree.

```python
result = pix.acquire_frames(count=2, sec=0.5)
for frame in result["frames"]:
    data = frame["data"]
    print(frame["name"], data.shape, frame["nonzero"])

stored = pix.get_frames()
sdk_result = pix.get_acq_frames()
print(len(stored), sdk_result["frame_count"])
```

Here `pix` is an already connected `MiniPixCtrl` instance. `get_acq_frames()` requires an active connection and acquisition data available in the SDK.

## Callback and readout timing

For Frames acquisitions, providing a `callback`, TIFF saving, or HDF5 saving registers `PX_EVENT_ACQ_FINISHED`. On each completion event, the latest frame is read into Python history, and the callback receives its frame dictionary when provided. Without any of these options, Frames acquisition reads the SDK frames after acquisition completes. **Both paths are designed to retain the results in Python history.**

Integral acquisition calls SDK `doSimpleIntegralAcquisition()`; it does not sum frames in Python. On successful completion, if an SDK frame is available, it stores the last frame and performs saving and callback invocation once when requested. It does not invoke the callback for intermediate integration steps.

## State, exceptions, and threading

`acquire()` clears Python frame history at the start and resets the requested and completed counters in `state()`. `stop()` calls SDK `abortOperation()` when an acquisition is running. `state()["finished_count"]` counts retained frames for Frames acquisitions, but is set to the requested count after successful Integral acquisition. It therefore differs in meaning from the result's `frame_count`.

SDK errors, exceptions in user callbacks, and saving errors can propagate. `state()["last_error"]` is updated when an exception occurs. The source alone does not establish thread-safety guarantees for callbacks or concurrent stop requests on physical hardware.

## Saving

TIFF is saved per frame, HDF5 appends to the `frames` dataset, and PIXet native uses SDK saving. Do not assume the on-disk representation matches the Python return dictionary. See [Acquisition and saving](acquisition.md).
