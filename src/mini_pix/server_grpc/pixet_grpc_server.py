#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Optional

import grpc
from grpc import channel_ready_future

from grpc_frame.grpc_server import create_grpc_server
from mini_pix.config import Config
from mini_pix.pixet_ctrl import MiniPixCtrl
from x_logger import XLogger


def pixet_grpc_server(
    *,
    grpc_host: str,
    grpc_port: int,
    auto_connect: bool = True,
    logger: Optional[Any] = None,
    log_level: Optional[str] = None,
) -> None:
    if logger is None:
        import logging

        log_level = log_level or "INFO"
        logging.basicConfig(level=log_level.upper())
        logger = logging.getLogger(__name__)

    ctrl = MiniPixCtrl(
        logger=logger,
        log_level=log_level,
    )
    server = None

    try:
        if auto_connect:
            ctrl.connect()

        server = create_grpc_server(
            ctrl_obj=ctrl,
            logger=logger,
            log_level=log_level,
            max_workers=10,
        )

        bind_addr = f"{grpc_host}:{grpc_port}"
        ret = server.add_insecure_port(bind_addr)
        if ret == 0:
            raise RuntimeError(f"bind failed: {bind_addr}")

        server.start()
        logger.info(f"gRPC start OK: {bind_addr}")

        ch = grpc.insecure_channel(bind_addr)
        channel_ready_future(ch).result(timeout=2.0)
        logger.info("gRPC self-check OK")

        server.wait_for_termination()

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")

    finally:
        if server is not None:
            server.stop(grace=None)

        try:
            ctrl.disconnect()
        except Exception:
            pass

        logger.info("gRPC server stopped")


pixet_server = pixet_grpc_server


if __name__ == "__main__":
    config = Config("mini_pix.yaml")

    logger_ = XLogger(
        log_level=config.LOGGER_LEVEL,
        logger_name=config.SERVER_LOGGER_NAME,
    )

    pixet_grpc_server(
        grpc_host=config.SERVER_IP,
        grpc_port=config.SERVER_PORT,
        logger=logger_,
        log_level=config.LOGGER_LEVEL,
    )
