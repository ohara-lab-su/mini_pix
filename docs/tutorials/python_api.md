# Python API

## MiniPixCtrl

`MiniPixCtrl` は `pixet_ctrl.py` に実装された MiniPIX / Timepix 用の上位制御クラスです。

```python
from mini_pix.pixet_ctrl import MiniPixCtrl

pix = MiniPixCtrl()
```

### `__init__(logger=None, log_level=None)`

制御オブジェクトを作成します。この時点では PIXet core へ接続しません。

引数:

・ `logger` : 任意の logger。未指定時は標準 `logging` を使う  
・ `log_level` : logger 未指定時のログレベル。未指定時は `INFO`  

内部状態として `_dev`、`_pixcfg`、`_pixet` は `None` で初期化されます。

### `connect() -> bool`

PIXet core を起動し、検出器へ接続します。

成功時は `True`、失敗時は `False` を返します。失敗扱いになる主な条件は次のとおりです。

・ `pixet.devices()` が空  
・ 先頭デバイスの `fullName()` が `FileDevice 0`  
・ `pixCfg.setModeAll()` に失敗  
・ `pixCfg.setToDevice()` に失敗  

接続成功時には、全ピクセルが `TOT` モードに設定されます。

### `disconnect()`

PIXet core を終了します。

`_pixet` が存在する場合は `exitPixet()` を試み、その後 `pypixet.exit()` を呼びます。最後に `_dev`、`_pixcfg`、`_pixet` を `None` に戻します。

## Detector setting API

### `set_mode_all(mode: str) -> bool`

全ピクセルの測定モードを変更します。

指定可能な `mode` は次の4種類です。

| mode | PIXet 定数 | 意味 |
|---|---|---|
| `COUNT` | `PX_TPXMODE_MEDIPIX` | 一定時間内のヒット数を記録する |
| `TOT` | `PX_TPXMODE_TOT` | Time over Threshold。しきい値超過時間幅を記録する |
| `TOA` | `PX_TPXMODE_TIMEPIX` | Time of Arrival。しきい値を超えた時刻を記録する |
| `ONEHIT` | `PX_TPXMODE_1HIT` | 最初の1ヒットのみ記録する |

実装上は `pixCfg.setModeAll()` を呼び、その後 `pixCfg.setToDevice()` でデバイスへ反映します。

注意: 未定義の `mode` を渡すと辞書参照で例外になります。呼び出し側では上記の文字列に限定してください。

### `set_threshold(threshold_kev: float) -> bool`

検出器のしきい値を keV 単位で設定します。

```python
pix.set_threshold(6.0)
```

内部では次を呼びます。

```python
dev.setThreshold(0, threshold_kev, pixet.PX_THLFLG_ENERGY)
```

chip index は現状 `0` 固定です。

### `set_clock(clock_mhz: float) -> bool`

Timepix clock を MHz 単位で設定します。

```python
pix.set_clock(9.66667)
```

内部では `dev.setTimepixClock(clock_mhz)` を呼びます。

### `set_bias(bias_volt: float) -> bool`

バイアス電圧を V 単位で設定します。

```python
pix.set_bias(150.0)
```

内部では `dev.setBias(bias_volt)` を呼びます。

## Acquisition API

### `simple_acq(count, sec, name="example.png", file_type="AUTODETECT", *, save_file=True, return_data=False)`

PIXet の通常 frame モードで指定枚数のフレームを取得します。

```python
result = pix.simple_acq(
    count=1,
    sec=3.0,
    name="example.png",
    file_type="PNG",
    save_file=True,
)
```

引数:

・ `count` : 取得フレーム数  
・ `sec` : 1フレームあたりの露光時間  
・ `name` : 保存ファイル名  
・ `file_type` : PIXet の保存形式  
・ `save_file` : ファイル保存するかどうか  
・ `return_data` : 現状の実装では参照されていない  

指定可能な `file_type` は次のとおりです。

| file_type | PIXet 定数 |
|---|---|
| `PNG` | `PX_FTYPE_PNG` |
| `TPX3_PIXELS` | `PX_FTYPE_TPX3_PIXELS` |
| `BINARY_FRAME` | `PX_FTYPE_BINARY_FRAME` |
| `NONE` | `PX_FTYPE_NONE` |
| `AUTODETECT` | `PX_FTYPE_AUTODETECT` |

`save_file=False` の場合、PIXet には空の `output_name` を渡します。`save_file=True` かつ `file_type="NONE"` の場合も `output_name` は空文字列になります。

戻り値は `doSimpleAcquisition()` 成功時に dict です。失敗時は `False` を返します。

```python
{
    "rc": 0,
    "saved_file": "example.png",
    "frame_count": 1,
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

## Frame read API

### `get_acq_frame_count() -> int`

PIXet core 内部に保持されている acquisition frame 数を返します。

内部では `dev.acqFrameCount()` を呼びます。

### `get_acq_frames(idx=None) -> dict`

PIXet core 内部に保持されている acquisition frame を読み出します。

`idx=None` の場合は全フレームを読み出します。`idx` に整数を指定した場合は、その1フレームのみを読み出します。

戻り値:

```python
{
    "frame_count": 1,
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

### `get_frame_size(frame, data_len) -> Tuple[int, int]`

frame の幅と高さを取得します。

まず `frame.width()` / `frame.height()` を試し、次に `_dev.width()` / `_dev.height()` を試します。どちらでも取得できない場合は `data_len` の平方根から正方形画像として推定します。推定できない場合は `RuntimeError` を送出します。

## 内部補助 API

### `_frame_to_dict(frame) -> dict`

PIXet frame を Python dict に変換します。

戻り値の項目:

・ `name` : `frame.frameName()`。取得できない場合は `frame`  
・ `width` : frame 幅  
・ `height` : frame 高さ  
・ `data` : `frame.data()` を list 化したピクセル値  
・ `subframes` : `frame.subFrames()` から取得した subframe のリスト  

subframe も同様に `name`、`width`、`height`、`data` を持ちます。

## 未実装 API

次のメソッドは定義だけがあり、現状は `pass` です。

・ `get_acq_data_count()`  
・ `get_acq_data(idx)`  
・ `simple_int_acq(count, sec, name="example.png", file_type="NONE", *, save_file=True, return_data=False)`  

これらはドキュメント上でも未実装として扱います。
