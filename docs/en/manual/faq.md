# Frequently asked questions

<a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/faq.html">日本語</a>

## Which detector is used?

**MiniPIX-D08-W0313**, with a Timepix chip, a 500 µm silicon sensor, and readout serial number 2746. Do not substitute specifications for Timepix3 or a 300 µm sensor.

## Why is `FileDevice 0` reported?

It is a PIXet file device; the controller rejects it as a physical detector. Check USB, drivers, and device detection in PIXet.

## Does `set_threshold()` accept raw THL?

No. It accepts **keV**. Do not pass the certificate's THL=691 as the argument.

## Why does Integral return one image?

It uses PIXet's integral acquisition and retains the final image, rather than summing all frames in Python.

## Are ToT values expressed in keV?

Not necessarily. Verify the energy calibration and PIXet's data representation.

## Is 55 fps guaranteed?

No. It is a product maximum; dead time, storage, and SDK processing affect practical throughput.

Sources: individual calibration certificate, product datasheet, supplied `pixet_ctrl.py`.
