# PIXet Python SDK と制御

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/pixet_sdk.html">English</a>

`pixet_ctrl.py` は `pypixet` を利用するローカル制御ラッパーである。PIXet Pro GUIの全機能を実装するものではない。初期化は `pypixet.start()`、終了は `pypixet.exit()` で行い、接続デバイスの `pixCfg()` を保持する。

| 公開メソッド | 役割 |
|---|---|
| `connect()` / `disconnect()` | 接続・終了 |
| `set_mode_all(mode)` | `Counting` / `Energy` / `Time` をPIXet定数へ変換 |
| `set_threshold(threshold_kev)` | エネルギーしきい値をkeV単位で指定 |
| `set_clock(clock_mhz)` | Timepixクロックの設定 |
| `set_bias(bias_volt)` | センサーバイアスの設定 |
| `acquire_frames(count, sec, ...)` | フレーム取得 |
| `acquire_integral(count, sec, ...)` | PIXetネイティブの積算取得 |
| `stop()` / `state()` | 停止・状態照会 |

`set_mode_all()` はPIXetの `PX_TPXMODE_MEDIPIX`、`PX_TPXMODE_TOT`、`PX_TPXMODE_TIMEPIX` に対応する。**しきい値はTHL DAC値ではなくkeV**を受け取る。`set_clock()` と `set_bias()` は要求値をPIXet SDKへ渡すが、入力値の安全範囲チェックはこの実装にはない。実機校正とメーカー仕様に基づいて設定する。

本コードの `set_bias()` は呼び出し先の戻り値を検査するが、測定後の実測バイアスや漏れ電流を読み戻す機能はない。PIXet SDKのAPI全体については、配布SDKに付属する資料を参照すること。

出典：添付 `pixet_ctrl.py`、PIXet Pro User's Manual pp.8–9, 13。
