#!/usr/bin/env python

# モジュールディレクトリを別の場所に置くときでもつかえる

# python >= 3.8
# import os
# pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
# os.add_dll_directory(pixet_dir)
# import site
# site.addsitedir(pixet_dir)
# import pypixet
# print("OK")

# python <= 3.7
import os
import site
pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

# Python 3.7 では add_dll_directory は使えないため PATH を変更
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir) # .pyd を import 可能にする
import pypixet
print("OK")