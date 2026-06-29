# CHANGELOG

## 2026.06.29, v0.0.1, nakada

・ grpc_frame の DeviceProxy に対応
・ mini_pix.server_grpc import 時に MiniPixCtrl を DeviceProxy 登録するように変更
・ DeviceProxy 登録先を ese774_frame ではなく grpc_frame に変更
・ SyncPixetGrpcClient / AsyncPixetGrpcClient を DeviceProxy から生成できるように変更
・ server_grpc/make_pyi.py で grpc_frame.make_pyi_device_proxy を使って __init__.pyi を生成するように変更
・ __init__.pyi は手書きせず、make_pyi.py による生成物として扱う方針に整理

## 2026.03.25, v0.0.0, nakada