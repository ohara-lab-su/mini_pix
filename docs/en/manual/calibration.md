# D08-W0313 individual calibration

<a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/calibration.html">日本語</a>

This page records the **individual** D08-W0313 calibration protocol dated 2025-02-11. Never reuse these factory calibration values for another detector. The listed PIXet version, **1.7.8.936**, is the calibration-time version and may differ from the runtime SDK.

| Item | Certificate value |
|---|---:|
| Timepix clock | 10.0 MHz |
| Ikrum | 1 |
| FBK | 156 |
| THL Coarse | 8 |
| Preamp | 225 |
| Equalization mean THL | 751.666 |
| Equalization standard deviation | 2.250 |
| Equalization masked pixels | 2 |
| Final THL | 707 |
| Threshold calibration A / B | 11.831 / 49.262 |
| Minimum threshold | 3.697 keV |
| THL at 5 keV | 691.585 (summary: THL=691) |
| Bad pixels under X-ray test | 83 |
| Largest bad-pixel cluster | 66 |
| Ten-minute stability | 99.469% |
| ToT energy resolution σ near 60 keV | 2.728 keV |

The digital/bias test found zero bad pixels, while the X-ray test found 83: **these are different tests, not conflicting measurements of one metric**. Bias leakage was tested from 15 to 150 V; the tabulated leakage current is 0.0000 µA at each point, which does not establish a universal zero-leakage guarantee.

The mean ToT energy calibration coefficients are A=1.642, B=22.945, C=19.630, and T=4.368. These are certificate calibration parameters, **not** values to pass directly to `set_threshold()`. The Python API's `set_threshold(threshold_kev)` requests a threshold in **keV** through PIXet.

Both imaging (Counting) and tracking (Energy) are classified **B / Usable** for this unit; this does not guarantee performance under every experimental condition.

Source: D08-W0313 Calibration Protocol pp. 1–4.
