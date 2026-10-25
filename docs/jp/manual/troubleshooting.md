# 問題の切り分け

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/troubleshooting.html">English</a>

## 接続できない

まずメーカーPIXet Pro GUIで物理デバイスが見えるか確認する。次にUSB接続、ドライバー、SDKとPythonのビット数、コードに固定されたSDKディレクトリを確認する。`connect()` は列挙された最初のデバイスを選択するため、複数接続時はログの個体情報を確認する。

## `No physical detector found` / `FileDevice 0`

実装はファイルデバイスを拒否する。GUI側で実機認識を確認する。ファイルデバイスをD08-W0313と誤認しない。

## `setThreshold` / `setBias` / `setTimepixClock` が失敗

戻り値 `rc` と `lastError()` を確認する。校正プロトコルのTHL DAC値とAPIのkeV値を混同しない。バイアスの変更前に実機の適合条件を確認する。

## 測定途中でエラーになる

`state()` の状態とエラー文字列を確認する。TIFF/HDF5の保存先権限、空き容量、データ量、callbackの例外を切り分ける。取得処理は同期であり、停止の呼び出し元にも注意する。

## 画像の画素値が想定と違う

Counting、Energy/ToT、Time/ToAのモードとしきい値・校正を確認する。ToTを未校正のままエネルギー値として扱わない。

出典：添付 `pixet_ctrl.py`、MiniPIX Datasheet、PIXet Pro User's Manual。
