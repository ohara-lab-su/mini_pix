# Device specifications and safety

<a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/hardware.html">日本語</a>

The actual detector targeted by this project is **MiniPIX-D08-W0313**. Its individual calibration report identifies the readout as MiniPIX (serial number 2746), a **Timepix** chip, a **500 µm silicon sensor**, and model **MNXTXS-XP5210520**. Do not confuse this unit with the commonly described 300 µm silicon variant.

| Parameter | D08-W0313 |
|---|---|
| Matrix | 256 × 256 pixels |
| Pixel pitch | 55 µm (with edge/corner exceptions) |
| Nominal sensitive dimensions | Approximately 14.08 × 14.08 mm² |
| Interface | USB 2.0 High-Speed |
| Readout chip | Timepix (not Timepix3) |
| Sensor | 500 µm silicon |
| Readout modes | Event / ToT / ToA |
| Product maximum frame rate | 55 fps (typical readout time 19 ms) |

The product's 55 fps rating is an upper limit, not a guaranteed rate for Python control, storage, or communication. No signal is collected during frame readout. **MiniPIX is not a certified dosimeter** and must not be the sole basis for radiation-protection decisions.

Specified operating conditions are 0–50 °C and below 85% relative humidity without condensation. The datasheet calls for external temperature stabilization at **22 °C** using a cooling plate or Peltier element. The device shuts down when chip or CPU temperature exceeds 55 °C. USB hubs may reduce stability or performance.

**Never touch or clean the sensor.** Take extreme care around exposed wire bonds and when removing the protective cover. Mechanical damage to wire bonds is not covered by the warranty. Vacuum compatibility must be confirmed with the manufacturer for the specific device.

Sources: MiniPIX Standard Datasheet pp. 2–8; Quick Start Guide p. 2; D08-W0313 Chip Detail p. 1; Calibration Protocol p. 1.
