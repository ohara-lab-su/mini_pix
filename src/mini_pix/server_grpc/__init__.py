#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""mini_pix.server_grpc の公開層と DeviceProxy 登録である。"""

from typing import Any, Optional

from grpc_frame import DeviceProxy, register_device_proxy

from mini_pix.server_grpc.async_pixet_grpc_client import AsyncPixetGrpcClient
from mini_pix.server_grpc.sync_pixet_grpc_client import SyncPixetGrpcClient

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


def pixet_grpc_server(
    *,
    grpc_host: str,
    grpc_port: int,
    auto_connect: bool = True,
    logger: Optional[Any] = None,
    log_level: Optional[str] = None,
) -> None:
    """サーバー実装を遅延 import して MiniPIX gRPC server を起動する。"""
    from mini_pix.server_grpc.pixet_grpc_server import pixet_grpc_server as _server

    _server(
        grpc_host=grpc_host,
        grpc_port=grpc_port,
        auto_connect=auto_connect,
        logger=logger,
        log_level=log_level,
    )


def pixet_server(
    *,
    grpc_host: str,
    grpc_port: int,
    auto_connect: bool = True,
    logger: Optional[Any] = None,
    log_level: Optional[str] = None,
) -> None:
    """pixet_grpc_server の互換名。"""
    pixet_grpc_server(
        grpc_host=grpc_host,
        grpc_port=grpc_port,
        auto_connect=auto_connect,
        logger=logger,
        log_level=log_level,
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
