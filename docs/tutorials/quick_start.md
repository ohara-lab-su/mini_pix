# Quick Start

## 前提

`MiniPixCtrl` は Windows 上の PIXet Pro Python API を前提にしています。現状の `pixet_ctrl.py` では、PIXet API の場所が次のように固定されています。

```python
pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"
```

Python 3.7 では `os.add_dll_directory()` が使えないため、実装では `PATH` に PIXet API ディレクトリを追加し、`site.addsitedir()` で `.pyd` を import 可能にしています。

## 最小例

```python
from mini_pix.pixet_ctrl import MiniPixCtrl

pix = MiniPixCtrl()

ok = pix.connect()
if not ok:
    raise RuntimeError("MiniPIX detector connection failed")

pix.set_mode_all("TOT")
pix.set_threshold(6.0)     # keV
pix.set_bias(150.0)        # V
pix.set_clock(9.66667)     # MHz

result = pix.simple_acq(
    count=1,
    sec=3.0,
    name="example.png",
    file_type="PNG",
    save_file=True,
    return_data=False,
)

pix.disconnect()
```

## 接続の流れ

`connect()` は次の処理を行います。

・ `pypixet.start()` で PIXet core を起動する  
・ `pypixet.pixet` を取得する  
・ `pixet.devices()` でデバイス一覧を取得する  
・ デバイスがない場合は `False` を返す  
・ 先頭デバイスが `FileDevice 0` の場合は物理検出器なしとして `False` を返す  
・ `deviceInfo()` でデバイス情報をログ出力する  
・ `dev.pixCfg()` を取得する  
・ 全ピクセルを ToT モードに設定する  
・ `pixCfg.setToDevice()` で pixel configuration をデバイスへ反映する  

接続直後のデフォルト測定モードは `TOT` です。

## 撮像

通常の撮像は `simple_acq()` を使います。

```python
result = pix.simple_acq(
    count=10,
    sec=0.5,
    name="image.png",
    file_type="AUTODETECT",
    save_file=True,
)
```

`count` は取得するフレーム数、`sec` は各フレームの露光時間です。`save_file=False` の場合、PIXet の保存ファイル名には空文字列を渡します。

`simple_acq()` は PIXet の `doSimpleAcquisition()` を呼び出した後、`get_acq_frames()` で取得済みフレームを読み出し、dict として返します。

戻り値の基本形は次のとおりです。

```python
{
    "rc": 0,
    "saved_file": "image.png",
    "frame_count": 10,
    "frames": [
        {
            "name": "frame",
            "width": 256,
            "height": 256,
            "data": [...],
            "subframes": []
        }
    ]
}
```

## 終了処理

測定が終わったら `disconnect()` を呼びます。

```python
pix.disconnect()
```

`disconnect()` は可能であれば `pixet.exitPixet()` を呼び、その後 `pypixet.exit()` を呼んで、内部参照を `None` に戻します。
