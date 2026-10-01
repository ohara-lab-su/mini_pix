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
    """MiniPIX の VIEW 用 server-streaming。"""

    def __init__(
        self,
        ctrl: MiniPixCtrl,
    ) -> None:
        self._ctrl = ctrl

    def _stream_acquisition(
        self,
        count: int,
        sec: float,
        acquisition_type: str,
    ):
        frame_queue = queue.Queue()
        finished = object()

        def frame_callback(frame):
            frame_queue.put(
                (
                    "frame",
                    frame,
                )
            )

        def acquisition_worker():
            try:
                if acquisition_type == "integral":
                    self._ctrl.acquire_integral(
                        count=count,
                        sec=sec,
                        callback=frame_callback,
                    )
                else:
                    self._ctrl.acquire_frames(
                        count=count,
                        sec=sec,
                        callback=frame_callback,
                    )

                frame_queue.put(
                    (
                        "finished",
                        finished,
                    )
                )

            except Exception as error:
                frame_queue.put(
                    (
                        "error",
                        error,
                    )
                )

        worker = threading.Thread(
            target=acquisition_worker,
            name="MiniPixAcquisitionStream",
            daemon=True,
        )
        worker.start()

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
        """各完成フレームを順次送信する。"""
        yield from self._stream_acquisition(
            count=count,
            sec=sec,
            acquisition_type="frames",
        )

    def acquire_integral(
        self,
        count: int,
        sec: float,
    ):
        """PIXet が生成した最終積算フレームだけを送信する。"""
        yield from self._stream_acquisition(
            count=count,
            sec=sec,
            acquisition_type="integral",
        )


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

    stream_obj = _MiniPixStream(
        ctrl=ctrl,
    )

    server = create_grpc_server(
        ctrl_obj=ctrl,
        stream_obj=stream_obj,
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
