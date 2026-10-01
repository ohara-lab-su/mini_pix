import os
import site

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)

import numpy as np
import pypixet
import tifffile


pypixet.start()

try:
    pixet = pypixet.pixet
    devices = pixet.devices()

    if len(devices) == 0:
        raise RuntimeError("MiniPIX device was not found.")

    dev = devices[0]

    print("Device:", dev.fullName())

    ################
    TIME = 1
    THRESHOLD = 2.4
    BIAS = 150.0
    CLOCK = 9.66667
    OUTPUT = "frame.tiff"
    ################

    pixcfg = dev.pixCfg()

    pixcfg.setModeAll(pixet.PX_TPXMODE_MEDIPIX) # Counting
    # pixcfg.setModeAll(pixet.PX_TPXMODE_TOT) # Energy (ToT)
    dev.setThreshold(
        0,
        THRESHOLD,
        pixet.PX_THLFLG_ENERGY,  # Threshold in keV
        # pixet.PX_THLFLG_NONE, # Threshold as raw DAC value
    )
    dev.setBias(BIAS)
    dev.setTimepixClock(CLOCK)

    rc = dev.doSimpleAcquisition(
        1,
        TIME,
        # Memory only
        pixet.PX_FTYPE_NONE,
        "",

        # SDK file output
        # pixet.PX_FTYPE_AUTODETECT,
        # "pixet_output.png",
    )

    if rc != 0:
        raise RuntimeError(
            "doSimpleAcquisition failed: " + str(rc)
        )

    frame = dev.lastAcqFrameRefInc()

    try:
        data = np.asarray(frame.data()).reshape(256, 256)

        print("dtype:", data.dtype)
        print("shape:", data.shape)
        print("min:", data.min())
        print("max:", data.max())
        print("non-zero:", np.count_nonzero(data))

        tifffile.imwrite(
            OUTPUT,
            data,
            photometric="minisblack",
            metadata=None,
        )

        print("Saved:", OUTPUT)

    finally:
        frame.destroy()

finally:
    pypixet.exit()
