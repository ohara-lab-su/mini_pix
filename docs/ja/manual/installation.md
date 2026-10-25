# インストールと起動条件

<a href="https://ohara-lab-su.github.io/mini_pix/en/manual/installation.html">English</a>

MiniPIX-D08-W0313をUSBで接続する。センサー表面に触れず、保護カバーの取り扱いには注意する。メーカーのQuick Start Guideでは、Windows用ドライバーの `Drivers/setup.exe`、macOS用 `Drivers/D2xxHelper_v2.0.0.pkg`、Windows用PIXet Proの `Pixet/Windows/setup.exe` が配布媒体の例として示されている。これらは**当該ガイド作成時点の配布物名**であり、現在の配布物と同一とは限らない。

添付されたPython実装の実行環境は **Windows上のPIXet Python SDK** を前提とし、冒頭に `C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64` を指定する。`site.addsitedir()` と `PATH` の変更でSDKとDLLを検索可能にしてから `pypixet` を読み込む。必要なPythonパッケージはコードのimportから `pypixet`、`numpy`、`h5py`、`tifffile` と判断できる。SDKのPython ABIとDLLアーキテクチャは配布SDKに合わせる。

PIXet Pro GUIのインストールと、Python SDKがロードできることは別の確認事項である。まずメーカーのGUIで実機が見えるか確認し、その後Python側の `connect()` でデバイス情報が出るか確認する。**コードを変更せずに使用する場合、SDKの固定パスが実環境と一致している必要がある。**

出典：Quick Start Guide p.2、PIXet Pro User's Manual pp.4–5、添付 `pixet_ctrl.py` 冒頭。
