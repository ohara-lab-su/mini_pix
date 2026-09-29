from __future__ import annotations

from typing import Any, Optional, Sequence, Tuple

from grpc_frame import SyncGrpcClient
from mini_pix.server_grpc.async_pixet_grpc_client import AsyncPixetGrpcClient


class SyncPixetGrpcClient(AsyncPixetGrpcClient, SyncGrpcClient):
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

        self._grpc_simple_acq = self.simple_acq
        self.simple_acq = self._simple_acq_sync

    def _simple_acq_sync(
        self,
        count: int,
        sec: float,
        name: str = "example.png",
        *,
        save_file: bool = False,
        save_local: bool = True,
        return_data: bool = False,
    ):
        result = self._grpc_simple_acq(
            count,
            sec,
            name=name,
            save_file=save_file,
            return_data=True,
        )
        return self._finish_simple_acq(result, name, save_local, return_data)


if __name__ == "__main__":
    from x_logger import XLogger

    logger_ = XLogger(
        log_level="INFO",
        logger_name="SyncPixetGrpcClient",
    )

    client = SyncPixetGrpcClient(
        server_ip="127.0.0.1",
        server_port=50051,
        logger=logger_,
        log_level="INFO",
    )

    try:
        client.connect()
        client.set_mode_all("TOT")
        #client.set_threshold(1000)
        client.set_threshold(6.0)
        client.set_bias(150)  # V
        client.set_clock(9.66667)  # Mhz
        client.simple_acq(1, 3.0, "example.png")
    finally:
        try:
            client.disconnect()
        except Exception:
            pass
