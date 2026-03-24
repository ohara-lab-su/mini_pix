######################################################
import os
import site

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

# Python 3.7 では add_dll_directory は使えないため PATH を変更
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)  # .pyd を import 可能にする
######################################################
import pypixet

print("pixet core init...")

# Piext core の起動
pypixet.start()
# Pixet core のハンドル（メインオブジェクト）を取得
pixet = pypixet.pixet

# もし、 pixet.devices() だと全デバイス
# TPX3 デバイスのみ取得。
# pixet.deviceByName(name)
#   --> GUI で表示されるデバイス名の指定
# devices = pixet.devicesByType(pixet.PX_DEVTYPE_TPX3)
devices = pixet.devices()

if len(devices) == 0:
    raise RuntimeError("No devices found")

dev = devices[0]

print("device:")
print("  fullName :", dev.fullName())
print("  deviceType:", dev.deviceType())
print("  chipType  :", dev.chipType())

# --- DevInfo ---
di = pixet.DevInfo()
rc = dev.deviceInfo(di)

print("DevInfo:")
print("  rc     :", rc)
print("  name   :", di.name)
print("  serial :", di.serial)
print("  type   :", di.type)
print("  vendor :", di.vendor)

# ==========================================================
# Timepix (Mpx2) は setOperationMode を使わない
# → pixel configuration で mode を設定
# dev.setOperationMode(pixet.PX_TPX3_OPM_EVENT_ITOT)
# ==========================================================

pixcfg = dev.pixCfg()

# DAC 一覧
# 全pixelを ToT モードに設定
# 0 COUNT 一定時間内にヒットした回数（カウント数）を記録
# 1 TOT (Time Over Threshold) しきい値を超えていた時間幅を記録 → エネルギーに比例
# 2 TOA (Time Of Arrival) しきい値を超えた時刻を記録
# 3 ONEHIT 最初の1ヒットのみ記録

pixcfg.setModeAll(
    1,
)

# threshold
# 0: THL threshold level
# 1: FBK feedback
# 2: IKRUM preamp current
# 3: DISC discriminator bias
# 4: PREAMP preamp bias
pixcfg.setDAC(
    0,
    1200,
)

print("dev.doSimpleAcquisition (3 frames @ 1 sec) - start")
rc = dev.doSimpleAcquisition(
    3,  # count (Acqの回数=フレーム数)
    1,  # 測定時間
    pixet.PX_FTYPE_AUTODETECT,  # 保存形式
    "example.png",  # ファイル名
)
print("dev.doSimpleAcquisition - end:", rc, "(0 is OK)")

# pixet.PX_FTYPE_PNG
# pixet.PX_FTYPE_TPX3_PIXELS
# pixet.PX_FTYPE_BINARY_FRAME
# pixet.PX_FTYPE_NONE

# using only for old pxcore versions up-to 1.8.3
# - save settings, correct stop devices and core exit
# - use both lines
# pixet.exitPixet()

# some USB devices must be power cycled
# if it not used / important if third-party debug environment used
pypixet.exit()
