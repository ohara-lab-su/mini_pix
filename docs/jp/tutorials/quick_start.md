# クイックスタート — Python制御

<a href="https://ohara-lab-su.github.io/mini_pix/en/tutorials/quick_start.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/tutorials/quick_start.html">日本語</a>

## 対象と前提

本書は `mini_pix` の **Python制御**の説明であり、検出器の製品マニュアルの代替ではありません。実機は **MiniPIX D08-W0313**（Timepix、Si 500 µm、readout serial 2746）です。メーカーの個体校正記録と、添付の `pixet_ctrl.py` を根拠にしています。

現在のソース先頭ではWindows用 PIXet API のパスが `C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64` に固定されています。PIXet Pro本体の導入と、Python SDK `pypixet` の利用環境は区別してください。`h5py`、`numpy`、`tifffile` もインポートされます。SDKの配布条件や対応Pythonバージョンは実際に使用するPIXet APIの配布物で確認してください。

## 測定例

以下は添付ソースの公開APIだけを使用する例です。`logger` は必須です。測定モードとしきい値は明示的に設定します。**バイアス電圧は測定環境と安全手順に依存するため、例では自動設定しません。**

```python
import logging
from mini_pix.pixet_ctrl import MiniPixCtrl

logger = logging.getLogger("mini_pix")
logging.basicConfig(level=logging.INFO)
pix = MiniPixCtrl(logger=logger)

if not pix.connect():
    raise RuntimeError("Physical MiniPIX detector not found")

try:
    if not pix.set_mode_all("Counting"):
        raise RuntimeError("Mode configuration failed")
    if not pix.set_threshold(5.0):
        raise RuntimeError("Threshold configuration failed")

    result = pix.acquire_frames(count=2, sec=0.5)
    print(result["frame_count"])
    print(result["frames"][0]["data"].shape)
finally:
    pix.disconnect()
```

`connect()` は検出した先頭のデバイスを使用し、`FileDevice 0` を拒否しますが、**D08-W0313の個体番号は検証しません**。接続ログの `serial` を確認してください。接続時にToTモードへ自動変更する処理はありません。

## モードと保存

`set_mode_all()` に渡せる文字列は `"Counting"`、`"Energy"`、`"Time"` の3種類だけです。`set_threshold(5.0)` の引数は **keV** であり、校正記録の `THL=691` というDAC値ではありません。

`acquire_frames()` は各フレームを返し、`acquire_integral()` はPIXetによる積算結果を返します。後者はPython側で加算せず、callbackも最終結果に対して1回です。保存形式は `None`、`"TIFF"`、`"HDF5"`、`"PIXET_NATIVE"`。TIFFは保存ディレクトリ、HDF5とPIXet nativeはファイル名を `save_path` に指定します。HDF5のデータセット名は `frames` です。

## 参照

- [Python API](python_api.md)
- [測定方式](../manual/acquisition.md)
- [個体校正](../manual/calibration.md)

メーカー資料: D08-W0313 Calibration protocol, MiniPIX Datasheet, PIXet Pro User's Manual。