from __future__ import annotations

from typing import Any, Optional, Sequence, Tuple

from grpc_frame import SyncGrpcClient
from mini_pix.server_grpc.async_pixet_grpc_client import AsyncPixetGrpcClient


class SyncPixetGrpcClient(
    AsyncPixetGrpcClient,
    SyncGrpcClient,
):
    """MiniPIX 用 SyncGrpcClient。"""

    def __init__(
        self,
        server_ip: str,
        server_port: int,
        timeout_sec: Optional[float] = None,
        logger: Optional[Any] = None,
        log_level: Optional[str] = None,
        grpc_options: Optional[Sequence[Tuple[str, Any]]] = None,
        set_timeout_sec: Optional[float] = None,
    ) -> None:
        if timeout_sec is not None and set_timeout_sec is not None:
            raise ValueError(
                "timeout_sec and set_timeout_sec cannot be specified together"
            )

        effective_timeout_sec = set_timeout_sec

        if timeout_sec is not None:
            effective_timeout_sec = timeout_sec

        SyncGrpcClient.__init__(
            self,
            server_ip=server_ip,
            server_port=server_port,
            timeout_sec=effective_timeout_sec,
            logger=logger,
            log_level=log_level,
            grpc_options=grpc_options,
        )

        self._grpc_acquire_frames = self.acquire_frames
        self._grpc_acquire_integral = self.acquire_integral

        self.acquire_frames = self._acquire_frames_sync
        self.acquire_integral = self._acquire_integral_sync

    def _acquire_frames_sync(
        self,
        count: int,
        sec: float,
        name: str = "frame.tiff",
        *,
        save_local: bool = True,
        return_data: bool = False,
        save_format=None,
        save_path=None,
    ):
        result = self._grpc_acquire_frames(
            count,
            sec,
            save_format=save_format,
            save_path=save_path,
        )

        return self._finish_acquisition(
            result,
            name,
            save_local,
            return_data,
        )

    def _acquire_integral_sync(
        self,
        count: int,
        sec: float,
        name: str = "integral.tiff",
        *,
        save_local: bool = True,
        return_data: bool = False,
        save_format=None,
        save_path=None,
    ):
        result = self._grpc_acquire_integral(
            count,
            sec,
            save_format=save_format,
            save_path=save_path,
        )

        return self._finish_acquisition(
            result,
            name,
            save_local,
            return_data,
        )
