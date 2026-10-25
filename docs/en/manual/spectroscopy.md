# Energy measurements and spectroscopy

<a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/spectroscopy.html">日本語</a>

D08-W0313 uses a Timepix chip and a 500 µm silicon sensor. ToT mode measures the duration of threshold-crossing signals per pixel, but **conversion from ToT to deposited energy requires calibration**. The PIXet Pro manual documents DAC scans, threshold equalization, and clustering. These are GUI/PIXet capabilities; the supplied `MiniPixCtrl` does not automatically perform them.

The D08-W0313 certificate reports ToT calibration measurements with Fe, In, and Am, mean coefficients A=1.642, B=22.945, C=19.630, T=4.368, and an Am verification at 59.518 keV with σ=2.728 keV. **The coefficient application formula and location of per-pixel calibration data cannot be established from the supplied controller alone.** Do not claim that the controller performs an independently reconstructed calibration.

The datasheet's typical detectable X-ray energy range for silicon is 5–60 keV. This is not the same quantity as the unit's 3.697 keV minimum discrimination threshold. For reproducible spectroscopy, record the readout mode, threshold, bias, clock, exposure duration, and calibration state.

Sources: Calibration Protocol pp. 2–4; MiniPIX Datasheet p. 4; PIXet Pro User's Manual pp. 22–33.
