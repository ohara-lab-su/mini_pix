# pyd の依存DLL調査
import pefile

pe = pefile.PE(r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64\pypixet.pyd")

for entry in pe.DIRECTORY_ENTRY_IMPORT:
    print(entry.dll.decode())