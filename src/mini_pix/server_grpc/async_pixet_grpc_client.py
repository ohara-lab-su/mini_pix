from __future__ import annotations

from typing import Any, Optional

from grpc_frame import AsyncGrpcClient


class AsyncPixetGrpcClient(AsyncGrpcClient):
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
