import pypixet

print("pixet core init...")
pypixet.start()
pixet = pypixet.pixet

devices = pixet.devices()
dev = devices[0]

print("device:")
print("  fullName :", dev.fullName())
print("  deviceType:", dev.deviceType())
print("  chipType  :", dev.chipType())

rc, name, serial, dev_type, vendor = dev.getDevInfo()
print("DevInfo:")
print("  rc     :", rc)
print("  name   :", name)
print("  serial :", serial)
print("  type   :", dev_type)
print("  vendor :", vendor)

pixcfg = dev.pixCfg()
pixcfg.setModeAll(pixet.PX_TPXMODE_MEDIPIX)

rc = dev.setThreshold(
    0,
    5.0,
    pixet.PX_THLFLG_ENERGY,
)
print("setThreshold:", rc)

# 同一条件で5回測定し、各画像を別ファイルとして保存する
for i in range(1, 6):
    filename = f"example_{i}.png"

    print(f"dev.doSimpleAcquisition ({i}/5, 1 frame @ 1 sec) - start")
    rc = dev.doSimpleAcquisition(
        1,
        1,
        pixet.PX_FTYPE_AUTODETECT,
        filename,
    )
    print(
        f"dev.doSimpleAcquisition ({i}/5) - end:",
        rc,
        "(0 is OK)",
        filename,
    )

pypixet.exit1()