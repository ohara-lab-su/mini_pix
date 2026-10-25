# よくある質問

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/faq.html">English</a>

## どの検出器を使っているか？

**MiniPIX-D08-W0313**。Timepixチップ、500 µm Siセンサー、読み出し部シリアル2746である。Timepix3や300 µm Siの説明をそのまま適用しない。

## `FileDevice 0` が見える

PIXetが返すファイルデバイスであり、コードは物理検出器とみなさず接続失敗にする。USB接続、ドライバー、PIXet側のデバイス認識を確認する。

## しきい値の引数はTHLか？

`set_threshold()` の引数は **keV**。証明書のTHL=691をそのまま引数として渡さない。

## Integralで画像が1枚しかない

PIXetの積算測定を使用し、最終結果を1枚保持する設計である。Pythonで全フレームを足しているわけではない。

## ToTの値はkeVか？

必ずしもそうではない。エネルギー校正とPIXetのデータ表現を確認する。

## 最大55 fpsで必ず取得できるか？

いいえ。製品仕様の最大値であり、読み出しデッドタイム、保存、SDK処理によって実効速度は変わる。

出典：個体校正証明書、製品仕様書、添付 `pixet_ctrl.py`。
