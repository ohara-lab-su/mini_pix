######################################################
import os
import site
pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

# Python 3.7 では add_dll_directory は使えないため PATH を変更
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir) # .pyd を import 可能にする
######################################################
# PIXETDIR="C:\\Program Files\\PIXet Pro"
# import os
#os.chdir(PIXETDIR)
# Note: Alternative is using sys.path.append(PIXETDIR)
import pypixet

print("pixet core init...")
pypixet.start()
pixet=pypixet.pixet
devices = pixet.devicesByType(pixet.PX_DEVTYPE_TPX3)
dev = devices[0]
dev.setOperationMode(pixet.PX_TPX3_OPM_EVENT_ITOT)

print("dev.doSimpleAcquisition (3 frames @ 1 sec) - start")
# rc = dev.doSimpleAcquisition(3, 1, pixet.PX_FTYPE_AUTODETECT, "c:\\test-files\\example.png")
rc = dev.doSimpleAcquisition(3, 1, pixet.PX_FTYPE_AUTODETECT, "example.png")
print("dev.doSimpleAcquisition - end:", rc, "(0 is OK)")

# using only for old pxcore versions up-to 1.8.3
# - save settings, correct stop devices and core exit
# - use both lines
#pixet.exitPixet()

# some USB devices must be power cycled
# if it not used / important if third-party debug environment used
pypixet.exit()