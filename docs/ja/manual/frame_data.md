# 測定結果のデータ構造と取得タイミング

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/frame_data.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/manual/frame_data.html">日本語</a>

このページは `MiniPixCtrl` が返す **Pythonデータ**の仕様を説明する。検出器の校正方法やPIXet Pro画面操作の説明ではない。根拠は現行 `pixet_ctrl.py` の `_frame_to_dict()`、`_store_frame()`、`acquire()`、`get_acq_frames()` である。

## 測定の戻り値

`acquire()`、`acquire_frames()`、`acquire_integral()` は次のキーを持つ辞書を返す。

| キー | 内容 |
| --- | --- |
| `rc` | PIXet SDKの測定呼び出しの戻りコード（整数）。 |
| `acquisition_type` | `"frames"` または `"integral"`。 |
| `frame_count` | Python側に保持された結果フレーム数。要求回数 `count` と常に一致するとは限らない。 |
| `frames` | フレーム辞書のリスト。 |
| `saved_file` | 保存先。保存なしの場合は空文字列。TIFFではディレクトリ、HDF5ではファイルパス、PIXet nativeでは指定ファイル名。 |

`frames` の各要素は、`name`、`width`、`height`、`data`、`minimum`、`maximum`、`nonzero`、`subframes` を持つ。`data` は **NumPy配列**で、`shape == (height, width)`。SDKの配列をコピーしてから整形している。`minimum` と `maximum` は配列の最小値と最大値、`nonzero` は非ゼロ要素数である。`subframes` は、存在すれば `name`、`width`、`height`、`data` を持つ辞書のリストとなる。これらの値を、エネルギー校正済みのスペクトルやイベントリストと同一視してはならない。

## SDK内部の取得結果とPython履歴

`get_frame_count()`、`get_frame()`、`get_frames()`、`get_current_frame()` は **Python側に蓄積した履歴**を扱う。`get_acq_frame_count()`、`get_acq_frames(idx=None)` は **PIXet SDK側の取得結果**を読み取る。後者の戻り値は単なるリストではなく、`{"frame_count": 整数, "frames": リスト}` の辞書である。`idx` を指定すると `frame_count` は1となり、指定フレームを読み取る。SDK側の履歴数とPython側の履歴数が一致することは、API仕様上の前提にしない。

```python
result = pix.acquire_frames(count=2, sec=0.5)
for frame in result["frames"]:
    data = frame["data"]
    print(frame["name"], data.shape, frame["nonzero"])

stored = pix.get_frames()
sdk_result = pix.get_acq_frames()
print(len(stored), sdk_result["frame_count"])
```

上の例では `pix` は接続済みの `MiniPixCtrl` インスタンスとする。`get_acq_frames()` は接続が必要であり、SDK側に取得結果が存在することも必要である。

## コールバックと取得時点

Frames測定で `callback`、TIFF保存、HDF5保存のいずれかを指定すると、`PX_EVENT_ACQ_FINISHED` のイベントを登録し、完了イベントごとに最新フレームを読み取ってPython履歴に格納する。コールバックはフレーム辞書を受け取る。これらを指定しないFrames測定では、SDK測定終了後に `acqFrameCount()` を参照してフレームを読み取る。**いずれの経路でも履歴を保持する設計**である。

Integral測定ではSDKの `doSimpleIntegralAcquisition()` を呼び出し、Python側でフレームを加算しない。成功後にSDK側のフレームが存在する場合、最後の1フレームを格納し、指定があれば保存・コールバック呼び出しを1回実行する。積算途中のフレームごとにコールバックされるわけではない。

## 状態・例外・スレッド

`acquire()` は測定開始時にPython履歴を消去し、`state()` の要求数と完了数を初期化する。`stop()` は実行中にSDKの `abortOperation()` を呼ぶ。`state()` の `finished_count` は、Framesでは履歴の枚数、Integral成功時には要求回数に設定されるため、結果辞書の `frame_count` と意味が異なる。

SDKエラー、コールバック内の例外、保存エラーは測定例外として伝播し得る。`state()` の `last_error` は例外発生時に更新される。イベントコールバックを利用する際の呼出スレッドや停止との競合については、ソースコードだけから実機上の安全性を保証できない。

## 保存形式との関係

TIFFはフレーム単位、HDF5は `frames` データセットへの追記、PIXet nativeはSDKの保存処理を使用する。保存ファイルの内容をPythonの戻り値と同一形式だと仮定せず、詳細は [測定と保存](acquisition.md) を参照する。
