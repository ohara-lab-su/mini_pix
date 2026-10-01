#!/usr/bin/env python3
"""Start the MiniPIX gRPC device server."""

from mini_pix.config import Config
from mini_pix.server_grpc import pixet_grpc_server
from x_logger import XLogger


AUTO_CONNECT = True


def main() -> None:
    config = Config("mini_pix.yaml")

    logger = XLogger(
        log_level=config.LOGGER_LEVEL,
        logger_name=config.SERVER_LOGGER_NAME,
    )

    pixet_grpc_server(
        grpc_host=config.SERVER_IP,
        grpc_port=config.SERVER_PORT,
        auto_connect=AUTO_CONNECT,
        logger=logger,
        log_level=config.LOGGER_LEVEL,
    )


if __name__ == "__main__":
    main()
