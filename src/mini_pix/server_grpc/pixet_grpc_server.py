#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from typing import Any, Optional

import grpc
from grpc import channel_ready_future

from grpc_frame.grpc_server import create_grpc_server

from mini_pix.pixet_ctrl import MiniPixCtrl


def pixet_grpc_server(
    *,
    grpc_host: str,
    grpc_port: int,
    auto_connect: bool = True,
    logger: Optional[Any] = None,
    log_level: Optional[str] = None,
) -> None:
    """Start MiniPIX gRPC server."""
    if logger is None:
        import logging

        if log_level is None:
            log_level = "INFO"

        logging.basicConfig(
            level=log_level.upper()
        )
        logger = logging.getLogger(
            __name__
        )

    ctrl = MiniPixCtrl(
        logger=logger,
        log_level=log_level,
    )

    if auto_connect:
        ctrl.connect()

    server = create_grpc_server(
        ctrl_obj=ctrl,
        logger=logger,
        log_level=log_level,
        max_workers=10,
    )

    bind_addr = (
        str(grpc_host)
        + ":"
        + str(grpc_port)
    )

    ret = server.add_insecure_port(
        bind_addr
    )
    if ret == 0:
        raise RuntimeError(
            "bind failed: "
            + bind_addr
        )

    logger.info(
        "gRPC bind OK: "
        + bind_addr
    )

    server.start()

    ch = grpc.insecure_channel(
        bind_addr
    )
    channel_ready_future(
        ch
    ).result(
        timeout=2.0
    )

    logger.info(
        "gRPC self-check OK"
    )

    try:
        while True:
            time.sleep(
                1
            )

    except KeyboardInterrupt:
        logger.info(
            "KeyboardInterrupt"
        )

    finally:
        server.stop(
            grace=None
        )

        logger.info(
            "gRPC server stopped"
        )

        try:
            ctrl.disconnect()
        except Exception:
            pass


pixet_server = pixet_grpc_server
