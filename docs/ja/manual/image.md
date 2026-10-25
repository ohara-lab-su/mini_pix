# 画像データと保存形式

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/image.html">English</a>

`_frame_to_dict()` はPIXetフレームの `data()` をNumPy配列としてコピーし、`(height, width)` に整形する。各フレーム辞書には `name`、`width`、`height`、`data`、`minimum`、`maximum`、`nonzero`、`subframes` が入る。サブフレームがあれば個別に読み出して `subframes` に格納する。

保存形式は `None`、`TIFF`、`HDF5`、`PIXET_NATIVE` を指定できる。TIFFでは1フレームにつき1ファイルを保存し、表示用の8ビット変換を行わない。HDF5ではFrames測定のフレーム完成ごとに追記・flushし、Integral測定では最終積算フレームのみを保存する。PIXET_NATIVEはPIXet自身の保存処理へファイル名を渡す。

**データの解釈:** Countingの画素値はしきい値超過イベントの計数、ToT/Energyはしきい値を超えた信号の時間幅に関係する量、Time/ToAは到来時刻に関係する量である。**ToTの画素値を、個別校正なしでkeVと同一視してはならない。** 積算画像も同様に、モードと校正条件を記録して解釈する。

出典：添付 `pixet_ctrl.py`、MiniPIX Datasheet p.5、PIXet Pro User's Manual pp.8–9。
