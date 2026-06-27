#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""mini_pix.server_grpc の公開層と DeviceProxy 登録である。"""

from mini_pix.server_grpc.async_pixet_grpc_client import AsyncPixetGrpcClient
from mini_pix.server_grpc.sync_pixet_grpc_client import SyncPixetGrpcClient
from mini_pix.server_grpc.pixet_grpc_server import pixet_grpc_server
from mini_pix.server_grpc.pixet_grpc_server import pixet_server

from ese774_frame.clients import register_device_proxy


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


__all__ = [
    "DEVICE_PROXY_NAME",
    "DEVICE_PROXY_ALIASES",
    "AsyncPixetGrpcClient",
    "SyncPixetGrpcClient",
    "pixet_grpc_server",
    "pixet_server",
]
