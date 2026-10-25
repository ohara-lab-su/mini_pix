# MiniPIX / PIXet 制御ドキュメント

<a href="https://ohara-lab-su.github.io/mini_pix/en/tutorials/index.html">English</a> | <a href="https://ohara-lab-su.github.io/mini_pix/jp/tutorials/index.html">日本語</a>

このドキュメントは `pixet_ctrl.py` の `MiniPixCtrl` を基準にした MiniPIX 制御 API の説明です。

`MiniPixCtrl` は PIXet Pro の Python API である `pypixet` を直接扱う上位ラッパです。利用者側では PIXet SDK の低レベルオブジェクトを直接操作せず、接続、検出器設定、露光、フレーム取得を Python メソッドとして呼び出します。

```{toctree}
:maxdepth: 1

quick_start
architecture
python_api
grpc_intro
grpc
```

現状の実装範囲は次のとおりです。

・ PIXet core の起動と終了  
・ 先頭検出器への接続  
・ `FileDevice 0` の検出と物理検出器未接続時の失敗扱い  
・ 全ピクセルの測定モード設定  
・ しきい値、Timepix clock、bias の設定  
・ `doSimpleAcquisition()` による通常フレーム取得  
・ PIXet 内部メモリに残ったフレームの dict 化  

未実装のメソッドは API 一覧に明記しています。
