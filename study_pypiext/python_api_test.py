#import ctypes
#ctypes.WinDLL(r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64\pxcore.dll")

# # モジュールローカルディレクトリでpydを使えるか？確認
# import ctypes
# ctypes.WinDLL(r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64\pypixet.pyd")
# print("OK")

# 任意のディレクトリで指定のフォルダのpydが使えるものか調べる
# python のバージョンを pyd とそろえる必要がある。

# python >= 3.8
# import os
# import ctypes
# dll_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
# os.add_dll_directory(dll_dir)
# ctypes.WinDLL(r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64\pypixet.pyd")
# print("OK")

# python <= 3.7
import os
import ctypes
dll_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
os.environ["PATH"] = dll_dir + ";" + os.environ["PATH"]
ctypes.WinDLL(os.path.join(dll_dir, "pypixet.pyd"))
print("OK")