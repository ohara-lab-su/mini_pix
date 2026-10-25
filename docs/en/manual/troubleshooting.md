# Troubleshooting

<a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/troubleshooting.html">日本語</a>

## Cannot connect

First check whether the physical device appears in the manufacturer's PIXet Pro GUI. Then inspect USB, drivers, SDK/Python architecture, and the hard-coded SDK directory. Because `connect()` selects the first enumerated device, verify its logged identity when multiple devices are connected.

## `No physical detector found` / `FileDevice 0`

The controller rejects a file device. Confirm physical detection in the GUI; never identify a file device as D08-W0313.

## `setThreshold`, `setBias`, or `setTimepixClock` fails

Inspect the return code `rc` and `lastError()`. Do not confuse a THL DAC code with the API's keV threshold. Check device-specific safe conditions before changing bias.

## Acquisition fails

Inspect `state()` and its error string. Check TIFF/HDF5 output permissions, free space, data volume, and exceptions in callbacks. Acquisition is synchronous, so consider the context used to request a stop.

## Unexpected pixel values

Check the Counting, Energy/ToT, or Time/ToA mode, threshold, and calibration. Do not treat uncalibrated ToT as energy.

Sources: supplied `pixet_ctrl.py`, MiniPIX Datasheet, PIXet Pro User's Manual.
