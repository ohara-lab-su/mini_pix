from __future__ import annotations

from typing import Any, Optional

from grpc_frame import SyncGrpcClient


class PixetGrpcClient(SyncGrpcClient):
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

        super().__init__(
            server_ip=server_ip,
            server_port=server_port,
            timeout_sec=timeout_sec,
            logger=logger,
            log_level=log_level,
        )


if __name__ == "__main__":
    from x_logger import XLogger

    log_level_ = "INFO"
    logger_ = XLogger(
        log_level=log_level_,
        logger_name="MiniPixGrpcClient",
    )

    client = PixetGrpcClient(
        server_ip="127.0.0.1",
        server_port=50051,
        logger=logger_,
        log_level=log_level_,
    )
    client.set_mode_all("TOT")
    client.set_threshold(1000)
    client.simple_acq(1, 1.0, "example.png")
