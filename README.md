# README

## Pixset Install

## Downloads

- [Downloads](https://advacam.com/downloads/)

## GUI の Doc

- [PIXset](https://wiki.advacam.cz/wiki/PIXet)


## Python API

- Pixet の情報(python)
- https://wiki.advacam.cz/wiki/Pixet_SDK
- https://wiki.advacam.cz/wiki/Python_API

Pixset フォルダにある API の zip を展開するとえられる
doc PDF 集がある。

USB ファイルの Piext フォルダにある  ZIP ファイルを展開することで
得られる。pip や setup.py などは存在しないために、
基本的にモジュールファイル(zip解凍で得られる) があるところでも
python プログラムを実行するか、後述する形で
```site.addsitedir(pixet_dir)```
などとして使えるようにする

### モジュールの本体

- pypixet.pyd: 設定、測定、ステータス情報の取得など、すべての基本的なデバイス機能のための基本API
- pypxproc.pyd: ピクセル処理。クラスタリングおよびスペクトルイメージングオブジェクトで使用

### ログディレクトリ

プログラム実行したディレクトリの logs サブディレクトリ

### その他モジュールを使うときに必要になるファイル

- pixet.ini: プログラムと同じディレクトリ
```ini
[Settings]
Splash=false

[Hwlibs]
fitpix.dll
minipix.dll
widepix.dll
zem.dll
zest.dll
``` 

### 依存ファイル

xcore.dll の依存DLL
```text
mfc110.dll
mfcloop.dll
msvcp120.dll
msvcp140.dll
msvcr110.dll
msvcr120.dll
vccorlib140.dll
vcruntime140.dll
```

## Pixet の導入に関しての紆余曲折

### 付属USBにある主なファイル
- PIXet_Pro_1.8.3_Windows_x86_64: GUIアプリケーション本体（通常ユーザー用）
- API_PIXet_Pro_1.8.3_Windows_x86_64: 開発者向けパッケージ（Python / C / C++ から制御するためのSDK一式）

API_PIXet_Pro を展開したフォルダにて
python を実行すると（実行の仕方はいろいろある、後で記述する）、
以下のランタムがないのでうまく動かない。

```text
VCRUNTIME140.dll
VCRUNTIME140_1.dll
MSVCP140.dll
```

が足りない。
つまり、[Microsoft Visual C++ Redistributable 2015–2022 (x64)](https://learn.microsoft.com/ja-jp/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-c-v14-redistributable)を入れる必要がある。

しかし、基本ランタイムを入れても、まだ足りない。次に、pypiex モジュールの元である pyd を調査する。

```python
import pefile

# pyd の依存DLL調査
pe = pefile.PE(r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64\pypixet.pyd")

for entry in pe.DIRECTORY_ENTRY_IMPORT:
    print(entry.dll.decode())
```

で調査すると

```text
PS C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64> python .\b.py
python37.dll
MSVCP140.dll
WSOCK32.dll
WS2_32.dll
KERNEL32.dll
VCRUNTIME140.dll
VCRUNTIME140_1.dll
api-ms-win-crt-runtime-l1-1-0.dll
api-ms-win-crt-stdio-l1-1-0.dll
api-ms-win-crt-filesystem-l1-1-0.dll
api-ms-win-crt-time-l1-1-0.dll
api-ms-win-crt-heap-l1-1-0.dll
api-ms-win-crt-string-l1-1-0.dll
PS C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64>
```

となる。つまりpython3.7 で Pypiext はビルドされている。
つまり python3.7 を導入しないとこのモジュールは使えない。

```
pyenv install 3.7.9
```

問題は、3.7.9 では add_dll_directory が使えないのでパスを変更する
```python
# python <= 3.7
import os
import site
pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

# Python 3.7 では add_dll_directory は使えないため PATH を変更
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir) # .pyd を import 可能にする
import pypixet
print("OK")
```
とすると、git のプロジェクトは別のところにあるモジュールを使えるようになる。

## python のバージョンを pyd とそろえるときの情報調査スクリプト

### python >= 3.8
```python
# 任意のディレクトリで指定のフォルダのpydが使えるものか調べる
# python のバージョンを pyd とそろえる必要がある。

# python >= 3.8
import os
import ctypes
dll_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
os.add_dll_directory(dll_dir)
ctypes.WinDLL(r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64\pypixet.pyd")
print("OK")
```

### python < 3.7
```python
# 任意のディレクトリで指定のフォルダのpydが使えるものか調べる
# python のバージョンを pyd とそろえる必要がある。

# python <= 3.7
import os
import ctypes
dll_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
os.environ["PATH"] = dll_dir + ";" + os.environ["PATH"]
ctypes.WinDLL(os.path.join(dll_dir, "pypixet.pyd"))
print("OK")
```

## 任意の場所にあるモジュールを動かす方法

### python <= 3.8
```python
# モジュールディレクトリを別の場所に置くときでもつかえる
# python >= 3.8
import os
pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
os.add_dll_directory(pixet_dir)
import site
site.addsitedir(pixet_dir)
import pypixet
print("OK")
```
### pyton <= 3.7

```python
# モジュールディレクトリを別の場所に置くときでもつかえる

# python <= 3.7
import os
import site
pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

# Python 3.7 では add_dll_directory は使えないため PATH を変更
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir) # .pyd を import 可能にする
import pypixet
print("OK")
```

### pixed 2026.03 付属USBからの導入 module3

- python **3.7** の導入
- [Microsoft Visual C++ Redistributable 2015–2022 (x64)](https://learn.microsoft.com/ja-jp/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-c-v14-redistributable) 導入

以下の形で pypiext を使う
```python
import os
import site
pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir) # .pyd を import 可能にする

import pypixet
```

