#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import queue
import threading
import time
from typing import Any, Optional

import grpc
from grpc import channel_ready_future

from grpc_frame.grpc_server import create_grpc_server

from mini_pix.pixet_ctrl import MiniPixCtrl


class _MiniPixStream:
    """MiniPIX の取得結果を grpc_frame StreamCall へ渡す。"""

    def __init__(
        self,
        ctrl: MiniPixCtrl,
    ) -> None:
        self._ctrl = ctrl

    def _acquire(
        self,
        count: int,
        sec: float,
        acquisition_type: str,
    ):
        frame_queue = queue.Queue()

        def frame_callback(frame):
            frame_queue.put(
                (
                    "frame",
                    frame,
                )
            )

        def worker():
            try:
                if acquisition_type == "integral":
                    self._ctrl.acquire_integral(
                        count,
                        sec,
                        callback=frame_callback,
                    )

                else:
                    self._ctrl.acquire_frames(
                        count,
                        sec,
                        callback=frame_callback,
                    )

                frame_queue.put(
                    (
                        "finished",
                        None,
                    )
                )

            except Exception as error:
                frame_queue.put(
                    (
                        "error",
                        error,
                    )
                )

        acquisition_thread = threading.Thread(
            target=worker,
            name="MiniPixAcquisition",
            daemon=True,
        )
        acquisition_thread.start()

        while True:
            item_type, value = frame_queue.get()

            if item_type == "frame":
                yield value
                continue

            if item_type == "error":
                raise value

            if item_type == "finished":
                break

    def acquire_frames(
        self,
        count: int,
        sec: float,
    ):
        yield from self._acquire(
            count,
            sec,
            "frames",
        )

    def acquire_integral(
        self,
        count: int,
        sec: float,
    ):
        yield from self._acquire(
            count,
            sec,
            "integral",
        )


def pixet_grpc_server(
    *,
    grpc_host: str,
    grpc_port: int,
    auto_connect: bool = True,
    logger: Optional[Any] = None,
    log_level: Optional[str] = None,
) -> None:
    """
    Start MiniPIX gRPC server.
    """
    print("pixet_grpc_server")
    if logger is None:
        import logging

        if log_level is None:
            log_level = "INFO"

        logging.basicConfig(level=log_level.upper())
        logger = logging.getLogger(__name__)

    print("a" "")
    ctrl = MiniPixCtrl(
        logger=logger,
        log_level=log_level,
    )

    if auto_connect:
        ctrl.connect()

    stream_obj = _MiniPixStream(ctrl)

    server = create_grpc_server(
        ctrl_obj=ctrl,
        stream_obj=stream_obj,
        logger=logger,
        log_level=log_level,
        max_workers=10,
    )

    bind_addr = str(grpc_host) + ":" + str(grpc_port)

    ret = server.add_insecure_port(bind_addr)
    if ret == 0:
        raise RuntimeError("bind failed: " + bind_addr)

    logger.info("gRPC bind OK: " + bind_addr)

    server.start()

    ch = grpc.insecure_channel(bind_addr)
    channel_ready_future(ch).result(timeout=2.0)

    ch.close()

    logger.info("gRPC self-check OK")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")

    finally:
        server.stop(grace=None)

        logger.info("gRPC server stopped")

        try:
            ctrl.disconnect()
        except Exception:
            pass


pixet_server = pixet_grpc_server
