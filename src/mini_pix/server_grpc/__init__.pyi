from typing import Any, Literal, Optional, overload

from mini_pix.server_grpc.async_pixet_grpc_client import AsyncPixetGrpcClient
from mini_pix.server_grpc.sync_pixet_grpc_client import SyncPixetGrpcClient
from mini_pix.server_grpc.pixet_grpc_server import pixet_grpc_server, pixet_server

@overload
def DeviceProxy(
    device_class: Literal["mini_pix"],
    *args: Any,
    async_mode: Literal[False] = False,
    **kwargs: Any,
) -> SyncPixetGrpcClient: ...

@overload
def DeviceProxy(
    device_class: Literal["mini_pix"],
    *args: Any,
    async_mode: Literal[True],
    **kwargs: Any,
) -> AsyncPixetGrpcClient: ...

@overload
def DeviceProxy(
    device_class: Literal["pixet"],
    *args: Any,
    async_mode: Literal[False] = False,
    **kwargs: Any,
) -> SyncPixetGrpcClient: ...

@overload
def DeviceProxy(
    device_class: Literal["pixet"],
    *args: Any,
    async_mode: Literal[True],
    **kwargs: Any,
) -> AsyncPixetGrpcClient: ...

@overload
def DeviceProxy(
    device_class: Literal["MiniPix"],
    *args: Any,
    async_mode: Literal[False] = False,
    **kwargs: Any,
) -> SyncPixetGrpcClient: ...

@overload
def DeviceProxy(
    device_class: Literal["MiniPix"],
    *args: Any,
    async_mode: Literal[True],
    **kwargs: Any,
) -> AsyncPixetGrpcClient: ...

@overload
def DeviceProxy(
    device_class: Literal["MiniPixCtrl"],
    *args: Any,
    async_mode: Literal[False] = False,
    **kwargs: Any,
) -> SyncPixetGrpcClient: ...

@overload
def DeviceProxy(
    device_class: Literal["MiniPixCtrl"],
    *args: Any,
    async_mode: Literal[True],
    **kwargs: Any,
) -> AsyncPixetGrpcClient: ...

@overload
def DeviceProxy(
    device_class: Literal["pixet_grpc"],
    *args: Any,
    async_mode: Literal[False] = False,
    **kwargs: Any,
) -> SyncPixetGrpcClient: ...

@overload
def DeviceProxy(
    device_class: Literal["pixet_grpc"],
    *args: Any,
    async_mode: Literal[True],
    **kwargs: Any,
) -> AsyncPixetGrpcClient: ...

def DeviceProxy(
    device_class: str,
    *args: Any,
    async_mode: Optional[bool] = None,
    **kwargs: Any,
) -> Any: ...

__all__ = [
    "DeviceProxy",
    "DEVICE_PROXY_NAME",
    "DEVICE_PROXY_ALIASES",
    "AsyncPixetGrpcClient",
    "SyncPixetGrpcClient",
    "pixet_grpc_server",
    "pixet_server",
]
