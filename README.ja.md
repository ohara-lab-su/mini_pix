# mini_pix

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/mini_pix/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/mini_pix/blob/main/README.ja.md)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Fmini_pix-181717?logo=github)](https://github.com/ohara-lab-su/mini_pix/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/mini_pix/ja/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/)

ADVACAM MiniPIX / Timepix を PIXet Python API から制御し、ローカル制御および `grpc_frame` を用いたリモート制御を行うための
Python パッケージです。

v0.1.0 は、MiniPIX 実機を接続したサーバーと別マシンのクライアント間で、 以下の動作を確認した最初の基準版です。

- Frames 測定
- Integral 測定
- リモート VIEW
- クライアント側 TIFF / PNG 保存

## アーキテクチャ

`mini_pix` は、検出器を直接扱うローカル制御層と、gRPC を介したリモート制御層を分離しています。

```text
Client
  |
  | grpc_frame / gRPC
  v
MiniPIX Server
  |
  v
MiniPixCtrl
  |
  v
PIXet Python API (pypixet)
  |
  v
MiniPIX / Timepix
```

サーバー側では PIXet Python API と MiniPIX 実機が必要です。

クライアント側では PIXet Python API および `pypixet` は不要です。 `mini_pix.server_grpc` はクライアント API の import
時にサーバー実装を読み込まず、 `pixet_grpc_server` または `pixet_server` が必要になった時だけサーバー実装を遅延 import
します。

## v0.1.0 に至るまでの経緯

v0.1.0 は、従来の v0.0.x 系をそのまま拡張した版ではありません。

v0.0.4 までに DeviceProxy、Frames、Integral、gRPC client などは実装され、次版を v0.0.5
とする想定で開発を進めていました。しかし、それまでの確認にはX線を入れない試験が含まれており、通信や API
呼び出しが完了することと、検出器として正しい画像が得られることを十分に分離して検証できていませんでした。

その後、実際にX線を入れて PIXet Pro GUI と Python API の取得画像を比較したところ、Python 側が公式 GUI
の挙動を再現していないことが判明しました。このため旧実装へ修正を積み重ねず、PIXet Python API
の最小ローカルコードまで戻り、実機制御を段階的に再構築しました。

再設計の順序は、PIXet Pro GUI での基準動作確認、最小 API コード、calibration / device configuration、raw frame、GUI 表示、複数
frame、class 化、callback、保存、Integral、`MiniPixCtrl` への統合、最後に gRPC / remote VIEW、です。この再構築後の実装を v0.1.0
とし、以後の基準版とします。

### 再設計時のローカル検証コード

- `01a.py`: PIXet core 起動、実機認識、mode / threshold、`doSimpleAcquisition()` の基本動作を最小構成で確認。
- `01b_tiff.py`: GUI の基準条件に合わせ、`PX_FTYPE_NONE` から `frame.data()` を直接取得し raw TIFF として保存。SDK の画像出力と
  raw detector data を分離して確認。
- `01b_gui_memory.py`: memory frame を直接表示。raw data と表示処理を分離し、PIXet GUI と上下方向を合わせる処理、Auto /
  Manual range、Nearest / Smooth を検証。
- `01c_gui_memory.py`: device 初期化、設定、1 frame 取得を GUI から関数として分離。
- `01d_gui_function.py`: 複数 frame の一括取得と、測定終了後の全 frame 取得を関数として整理。
- `01e_gui_class.py`: PIXet / MiniPIX の初期化、設定、測定、終了処理を GUI 非依存 class にまとめ、制御層と表示層を分離。
- `01f_gui_callback.py`: `PX_EVENT_ACQ_FINISHED` を使い、Frames 測定中に各 frame を callback で取得。callback
  なしの測定終了後取得も維持。
- `01g_gui_save_intAcq.py`: TIFF / HDF5 / PIXet native、Stop / state、Integral を追加。Integral は
  `doSimpleIntegralAcquisition()` を使用し、Python 側では積算しない方式を確立。

この系列は別実装ではなく、現在の `pixet_ctrl.py`、`view_local.py`、`view_client.py` に至る実機検証・再設計の過程です。

## 主なモジュール

### `mini_pix.pixet_ctrl.MiniPixCtrl`

MiniPIX / Timepix のローカル制御クラスです。

gRPC、GUI、server/client 設定は扱わず、PIXet Python API を直接使用します。

主な機能:

- `connect()` / `disconnect()`
- `set_mode_all()`
- `set_threshold()`
- `set_clock()`
- `set_bias()`
- `acquire()`
- `acquire_frames()`
- `acquire_integral()`
- `stop()`
- `is_running()`
- `is_aborting()`
- `state()`
- `clear_frames()`
- `get_frame_count()`
- `get_frame()`
- `get_frames()`
- `get_current_frame()`
- `get_acq_frame_count()`
- `get_acq_frames()`

`MiniPixCtrl` の `logger` は必須です。

### Frames 測定

通常のフレーム測定です。

```python
result = ctrl.acquire_frames(
    count,
    sec,
)
```

PIXet の acquisition event を利用できる場合は、 `PX_EVENT_ACQ_FINISHED` ごとに最新フレームを取得し、callback に渡します。

### Integral 測定

```python
result = ctrl.acquire_integral(
    count,
    sec,
)
```

Integral は PIXet の `doSimpleIntegralAcquisition()` を使用します。 Python 側で Frames の画像を加算して Integral
を生成する実装ではありません。

callback を指定した場合も、Integral では最終積算フレームに対して1回だけ呼び出されます。

## フレームデータ

取得フレームは辞書として扱います。

主な要素は次のとおりです。

```text
name
width
height
data
minimum
maximum
nonzero
subframes
```

`data` は NumPy の2次元配列です。

検出器から取得した配列は保存用 raw data として保持し、 表示のための変換とは分離します。

## 保存

`MiniPixCtrl.acquire()` / `acquire_frames()` / `acquire_integral()` は、 サーバー側保存として次を扱います。

```text
NONE
TIFF
HDF5
PIXET_NATIVE
```

### TIFF

1 frame を 1 TIFF として保存します。

表示用の正規化などを行わず、取得した数値配列をそのまま `tifffile` で保存します。

### HDF5

Frames 測定ではフレームごとに dataset へ追記し、逐次 `flush()` します。

Integral 測定では最終積算フレームを保存します。

dataset の dtype は取得した NumPy 配列の dtype を使用します。

### PIXET_NATIVE

PIXet 自身のファイル保存機能を使用します。

## gRPC

### サーバー

`mini_pix.server_grpc.pixet_grpc_server()` が `MiniPixCtrl` を生成し、 `grpc_frame.grpc_server.create_grpc_server()`
に公開します。

通常の制御 API は unary RPC として公開されます。

Frames / Integral の逐次画像転送には `grpc_frame` の `StreamCall` を使用します。

サーバー起動例は `example/start_minipix_server.py` です。

```python
from mini_pix.config import Config
from mini_pix.server_grpc import pixet_grpc_server
from x_logger import XLogger

config = Config("mini_pix.yaml")

logger = XLogger(
    log_level=config.LOGGER_LEVEL,
    logger_name=config.SERVER_LOGGER_NAME,
)

pixet_grpc_server(
    grpc_host=config.SERVER_IP,
    grpc_port=config.SERVER_PORT,
    auto_connect=True,
    logger=logger,
    log_level=config.LOGGER_LEVEL,
)
```

### DeviceProxy

`mini_pix.server_grpc` は `grpc_frame.DeviceProxy` に MiniPIX client を登録します。

標準名:

```text
mini_pix
```

alias:

```text
pixet
MiniPix
MiniPixCtrl
pixet_grpc
```

同期 client の例:

```python
from mini_pix.server_grpc import DeviceProxy

client = DeviceProxy(
    "mini_pix",
    server_ip="10.170.10.38",
    server_port=50051,
    set_timeout_sec=30.0,
    async_mode=False,
)
```

`async_mode=False` では `SyncPixetGrpcClient`、 `async_mode=True` では `AsyncPixetGrpcClient` を使用します。

### Client-side save

`SyncPixetGrpcClient` / `AsyncPixetGrpcClient` の `acquire_frames()` と `acquire_integral()` は、クライアント側保存に対応します。

```python
client.acquire_frames(
    1,
    1.0,
    name="frame.tiff",
    save_local=True,
    return_data=False,
)
```

対応するクライアント側保存形式:

- `.tif`
- `.tiff`
- `.png`

TIFF は raw 数値配列を保存します。

PNG は表示用としてフレームごとに min-max 正規化し、 16 bit grayscale PNG として保存します。

## VIEW

### `example/view_local.py`

`MiniPixCtrl` を直接使用するローカル VIEW です。

gRPC を使用せず、`MiniPixCtrl` の callback からフレームを受け取ります。

### `example/view_client.py`

別マシンから gRPC 経由で使用する VIEW です。

- Frames / Integral 切り替え
- count / acquisition time 設定
- detector mode / threshold / bias / clock 設定
- `StreamCall` によるフレーム受信
- 受信済みフレームのローカル履歴
- slider と前後ボタンによる履歴表示
- Auto / Manual display range
- nearest / smooth 表示
- Stop

クライアント VIEW は `pypixet` を必要としません。

## example

### `measure_simple.py`

Frames 測定の同期クライアント例です。

現在のサンプル設定:

```text
Mode      : Counting
Threshold : 5.0 keV
Bias      : 150 V
Clock     : 9.66667 MHz
Count     : 1
Time      : 1.0 s
```

TIFF 保存が有効で、PNG 保存例はコメントとして残しています。

### `measure_integral.py`

Integral 測定の同期クライアント例です。

現在のサンプル設定:

```text
Mode      : Counting
Threshold : 5.0 keV
Bias      : 150 V
Clock     : 9.66667 MHz
Count     : 1
Time      : 10.0 s
```

TIFF 保存が有効で、PNG 保存例はコメントとして残しています。

### `start_minipix_server.py`

`mini_pix.yaml` を読み込み、MiniPIX gRPC server を起動します。

## 設定ファイル

`example/mini_pix.yaml` の現在の項目:

``` yaml
SERVER_IP: "10.170.10.38"
SERVER_PORT: 50051
CLIENT_LOGGER_NAME: "mini_pix_client"
SERVER_LOGGER_NAME: "mini_pix_server"
TIMEOUT: 30.0
LOGGER_LEVEL: "debug"
ASYNC_MODE: false
```

IP address などは使用環境に合わせて変更してください。

## v0.1.0 で確認済みの構成

v0.1.0 では、MiniPIX / PIXet を接続したサーバーと別マシンのクライアント間で、

- `view_client.py`
- `measure_simple.py`
- `measure_integral.py`

の動作を確認しています。

これは v0.1.0 の基準動作とします。

------------------------------------------------------------------------

## PIXet / pypixet セットアップ

## Calibration / device configuration

MiniPIX では Python API が import でき、実機が認識されるだけでは十分ではありません。対象個体に対応する device
configuration / calibration XML が正しくロードされることが重要です。

今回の対象は次の実機です。

```text
Device : MiniPIX D08-W0313
Serial : 2746
Chip   : Timepix
Sensor : Si, 500 µm
```

### X線実測で判明した問題

公式 PIXet Pro GUI では、次の条件で正常な画像を確認しました。

```text
Mode      : Counting
Threshold : 2.4 keV
Bias      : 150 V
Clock     : 9.66667 MHz
Time      : 1 s
```

同じ実機を Python API から操作した初期の最小コードでは、X線を入れた実測時に GUI
と同じ画像挙動を再現できませんでした。mode、threshold、bias、clock の値だけを合わせても解決せず、個体固有 XML
のロードが重要な差であることが判明しました。

### USB 付属 Calibration XML

付属USBには個体用ファイル

```text
Calibration/MiniPIX-D08-W0313.xml
```

があります。API 環境ではこれを PIXet API ディレクトリの `factory` に配置します。

```text
C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64
└─ factory
   └─ MiniPIX-D08-W0313.xml
```

この配置後、Python API の取得画像の挙動は公式 GUI にほぼ一致しました。

したがって v0.1.0 のサーバー環境では、Python 3.7、DLL、`pixet.ini` だけでなく、使用する MiniPIX 個体に対応する XML
の配置までをセットアップの一部として扱います。

### `factory` と `configs`

PIXet core は保存済みの `configs` を優先して読み、使用可能な設定がない場合に `factory` の個体初期設定を使用します。
`configs` は終了処理で生成・更新され、次回起動時の現在設定として使用されます。

したがって、`factory` の個体用 calibration XML と、PIXet が実行後に `configs` に保存した XML は役割が異なります。また、公式
GUI が使用・保存した XML と Python API 側で生成された XML には実際に項目・値の差が確認されたため、両者を同一ファイルとして扱いません。

この問題は単なるインストール上の注意ではなく、v0.0.x 系から v0.1.0
へ再設計する直接の契機です。以後、API/通信の成功や画像ファイル生成だけで検出器制御の正しさを判断せず、公式 GUI
と同じ実機・測定条件でX線画像を比較することを実機検証の基準とします。

以下は MiniPIX を直接接続するサーバー側のセットアップ情報です。

### PIXet Install

### Downloads

- [Advacam Downloads](https://advacam.com/downloads/)
- もしくは付属のUSB

### ドライバなどの導入

- シリアルドライバ: USB の Drivers ディレクトリ以下の setup を実行 (検出器は外した状態で入れる
- GUIの導入 & ドライバ: USB の Pixet/Pixet_pro_windows の実行
- 再起動

### Python API のための準備

- [Microsoft Visual C++ Redistributable 2015--2022 (x64)](https://learn.microsoft.com/ja-jp/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-c-v14-redistributable)

### Python API の導入

- python 3.7 が必要 ([pyenv-win](https://qiita.com/probabilityhill/items/9a22f395a1e93206c846) で導入をお勧めします)
- [Python API](#python-api-の導入など)
- `c:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64` を準備

## AdvaCam Docs

- [PIXet](https://wiki.advacam.cz/wiki/PIXet)
- [Pixet SDK](https://wiki.advacam.cz/wiki/Pixet_SDK)
- [Pixet Python API](https://wiki.advacam.cz/wiki/Python_API)

------------------------------------------------------------------------

## Python API の導入など

- Pixet の情報 (python)
- <https://wiki.advacam.cz/wiki/Pixet_SDK>
- <https://wiki.advacam.cz/wiki/Python_API>

Pixset フォルダにある API の zip を展開するとえられる doc PDF 集がある。

USB ファイルの Piext フォルダにある ZIP ファイルを展開することで 得られる。pip や setup.py などは存在しないために、
基本的にモジュールファイル (zip解凍で得られる) があるところでも python プログラムを実行するか、後述する形で
`site.addsitedir(pixet_dir)` などとして使えるようにする

### モジュールの本体

- pypixet.pyd: 設定、測定、ステータス情報の取得など、すべての基本的なデバイス機能のための基本API
- pypxproc.pyd: ピクセル処理。クラスタリングおよびスペクトルイメージングオブジェクトで使用

### ログディレクトリ

プログラム実行したディレクトリの logs サブディレクトリ

### その他モジュールを使うときに必要になるファイル

- pixet.ini: プログラムと同じディレクトリ

``` ini
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

API_PIXet_Pro を展開したフォルダにて python を実行すると（実行の仕方はいろいろある、後で記述する）、 以下のランタムがないのでうまく動かない。

```text
VCRUNTIME140.dll
VCRUNTIME140_1.dll
MSVCP140.dll
```

が足りない。
つまり、[Microsoft Visual C++ Redistributable 2015--2022 (x64)](https://learn.microsoft.com/ja-jp/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-c-v14-redistributable)
を入れる必要がある。

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

となる。つまりpython3.7 で Pypiext はビルドされている。 つまり python3.7 を導入しないとこのモジュールは使えない。

    pyenv install 3.7.9

問題は、3.7.9 では add_dll_directory が使えないのでパスを変更する

```python
# python <= 3.7
import os
import site

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

# Python 3.7 では add_dll_directory は使えないため PATH を変更
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)  # .pyd を import 可能にする
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

### python <= 3.7

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

------------------------------------------------------------------------

## 任意の場所にあるモジュールを動かす方法 (まとめ)

### python >= 3.8

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

### python <= 3.7

```python
# モジュールディレクトリを別の場所に置くときでもつかえる

# python <= 3.7
import os
import site

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

# Python 3.7 では add_dll_directory は使えないため PATH を変更
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)  # .pyd を import 可能にする
import pypixet

print("OK")
```

### PIXet 2026.03 付属USBからの導入 module3

- python **3.7** の導入
- [Microsoft Visual C++ Redistributable 2015--2022 (x64)](https://learn.microsoft.com/ja-jp/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-c-v14-redistributable)
  導入

以下の形で pypiext を使う

```python
import os
import site

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)  # .pyd を import 可能にする

import pypixet
```
