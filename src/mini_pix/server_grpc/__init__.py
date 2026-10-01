#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""mini_pix.server_grpc の公開層と DeviceProxy 登録である。"""

from mini_pix.server_grpc.async_pixet_grpc_client import AsyncPixetGrpcClient
from mini_pix.server_grpc.sync_pixet_grpc_client import SyncPixetGrpcClient

from grpc_frame import DeviceProxy, register_device_proxy


DEVICE_PROXY_NAME = "mini_pix"
DEVICE_PROXY_ALIASES = [
    "pixet",
    "MiniPix",
    "MiniPixCtrl",
    "pixet_grpc",
]


register_device_proxy(
    DEVICE_PROXY_NAME,
    async_client_cls=AsyncPixetGrpcClient,
    sync_client_cls=SyncPixetGrpcClient,
    default_async_mode=False,
    aliases=DEVICE_PROXY_ALIASES,
)


def __getattr__(name):
    """サーバー実装は必要になった時だけ読み込む。

    client-only 環境では pypixet を import しない。
    """
    if name == "pixet_grpc_server":
        from mini_pix.server_grpc.pixet_grpc_server import pixet_grpc_server

        return pixet_grpc_server

    if name == "pixet_server":
        from mini_pix.server_grpc.pixet_grpc_server import pixet_server

        return pixet_server

    raise AttributeError(
        "module {!r} has no attribute {!r}".format(__name__, name)
    )


__all__ = [
    "DEVICE_PROXY_NAME",
    "DEVICE_PROXY_ALIASES",
    "DeviceProxy",
    "AsyncPixetGrpcClient",
    "SyncPixetGrpcClient",
    "pixet_grpc_server",
    "pixet_server",
]
