from __future__ import annotations

from typing import Any, Optional

from grpc_frame import SyncGrpcClient
from mini_pix.server_grpc.async_pixet_grpc_client import AsyncPixetGrpcClient


class SyncPixetGrpcClient(
    SyncGrpcClient,
    AsyncPixetGrpcClient,
):
    def __init__(
        self,
        config: Optional[Any] = None,
        server_ip: Optional[str] = None,
        server_port: Optional[int] = None,
        timeout_sec: Optional[float] = None,
        logger: Optional[Any] = None,
        log_level: Optional[str] = None,
    ) -> None:
        if config is not None:
            server_ip = config.SERVER_IP
            server_port = config.GRPC_PORT

        if server_ip is None or server_port is None:
            raise ValueError("server_ip and server_port are required")

        SyncGrpcClient.__init__(
            self,
            server_ip=server_ip,
            server_port=server_port,
            timeout_sec=timeout_sec,
            logger=logger,
            log_level=log_level,
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
        client.set_threshold(1000)
        client.simple_acq(1, 1.0, "example.png")
    finally:
        try:
            client.disconnect()
        except Exception:
            pass
        # client.close()
