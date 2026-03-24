######################################################
import os
import site

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)
######################################################
import json
import hashlib
import struct
from pathlib import Path

import pypixet

print("pixet core init...")

pypixet.start()
pixet = pypixet.pixet

devices = pixet.devices()
if len(devices) == 0:
    raise RuntimeError("No devices found")

dev = devices[0]

print("device:")
print("  fullName :", dev.fullName())
print("  deviceType:", dev.deviceType())
print("  chipType  :", dev.chipType())

di = pixet.DevInfo()
rc = dev.deviceInfo(di)

print("DevInfo:")
print("  rc     :", rc)
print("  name   :", di.name)
print("  serial :", di.serial)
print("  type   :", di.type)
print("  vendor :", di.vendor)

pixcfg = dev.pixCfg()
pixcfg.setModeAll(
    pixet.PX_TPXMODE_TOT,
)

dev.setThreshold(
    0,
    5.0,
    pixet.PX_THLFLG_ENERGY,
)


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_data_bin(path, data):
    with open(path, "wb") as f:
        for value in data:
            f.write(struct.pack("<H", max(0, min(65535, int(value)))))


print("dev.doSimpleAcquisition - start")
rc = dev.doSimpleAcquisition(
    1,
    1,
    pixet.PX_FTYPE_BINARY_FRAME,
    "example.pbf",
)
print("dev.doSimpleAcquisition - end:", rc, "(0 is OK)")

if rc != 0:
    raise RuntimeError("doSimpleAcquisition failed")

frame = dev.acqFrameRefInc(0)
try:
    data = list(frame.data())
finally:
    try:
        frame.destroy()
    except Exception:
        pass

write_data_bin("example_from_data.bin", data)

saved_bytes = Path("example.pbf").read_bytes()
data_bytes = Path("example_from_data.bin").read_bytes()

result = {
    "saved_file": "example.pbf",
    "data_file": "example_from_data.bin",
    "saved_file_size": len(saved_bytes),
    "data_file_size": len(data_bytes),
    "saved_sha256": sha256_file("example.pbf"),
    "data_sha256": sha256_file("example_from_data.bin"),
    "same_bytes": saved_bytes == data_bytes,
    "saved_head_hex": saved_bytes[:64].hex(),
    "data_head_hex": data_bytes[:64].hex(),
    "data_head_values": data[:32],
}

print(json.dumps(result, ensure_ascii=False, indent=2))
Path("example_compare.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

pypixet.exit()
