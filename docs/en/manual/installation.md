# Installation and runtime requirements

<a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/installation.html">日本語</a>

Connect the MiniPIX-D08-W0313 over USB without touching the sensor; handle the protective cover carefully. The manufacturer's Quick Start Guide names `Drivers/setup.exe` for Windows, `Drivers/D2xxHelper_v2.0.0.pkg` for macOS, and `Pixet/Windows/setup.exe` for PIXet Pro on Windows. These are **distribution filenames from that edition of the guide**, not a guarantee about current packages.

The supplied Python controller assumes a **Windows PIXet Python SDK** at `C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64`. It modifies `PATH`, calls `site.addsitedir()`, and only then imports `pypixet`. Source imports additionally require `numpy`, `h5py`, and `tifffile`. The Python ABI and DLL architecture must match the distributed SDK.

Installing the PIXet Pro GUI and loading the Python SDK are separate checks. First verify detection in the manufacturer's GUI, then check the logged device information from `connect()`. **To use the controller without source changes, the hard-coded SDK path must match the installation.**

Sources: Quick Start Guide p. 2; PIXet Pro User's Manual pp. 4–5; supplied `pixet_ctrl.py` module header.
