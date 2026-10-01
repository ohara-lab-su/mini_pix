#!/usr/bin/env python3
from __future__ import annotations

import queue
import threading
from typing import Any, Dict, Iterator, Optional

import grpc
from grpc import channel_ready_future

from grpc_frame.grpc_server import create_grpc_server
from mini_pix.config import Config
from mini_pix.pixet_ctrl import MiniPixCtrl
from x_logger import XLogger


class MiniPixGrpcCtrl(MiniPixCtrl):
    """
    gRPC サーバーでのみ使用する MiniPixCtrl 派生クラス。

    MiniPixCtrl 本体には gRPC や通信処理を入れない。
    通常 API は MiniPixCtrl からそのまま継承し、VIEW 用の逐次転送だけを
    generator API として追加する。
    """

    def stream_frames(
        self,
        count: int,
        sec: float,
    ) -> Iterator[Dict[str, Any]]:
        frame_queue = queue.Queue()
        end_marker = object()
        errors = []

        def callback(frame):
            frame_queue.put(frame)

        def acquisition_worker():
            try:
                self.acquire_frames(
                    count=count,
                    sec=sec,
                    callback=callback,
                )
            except Exception as error:
                errors.append(error)
            finally:
                frame_queue.put(end_marker)

        worker = threading.Thread(
            target=acquisition_worker,
            daemon=True,
        )
        worker.start()

        while True:
            frame = frame_queue.get()

            if frame is end_marker:
                break

            yield frame

        worker.join()

        if len(errors) > 0:
            raise errors[0]

    def stream_integral(
        self,
        count: int,
        sec: float,
    ) -> Iterator[Dict[str, Any]]:
        """
        Integral は PIXet 内部で積算し、最終積算フレームだけを1回 yield する。
        """
        frame_queue = queue.Queue()
        end_marker = object()
        errors = []

        def callback(frame):
            frame_queue.put(frame)

        def acquisition_worker():
            try:
                self.acquire_integral(
                    count=count,
                    sec=sec,
                    callback=callback,
                )
            except Exception as error:
                errors.append(error)
            finally:
                frame_queue.put(end_marker)

        worker = threading.Thread(
            target=acquisition_worker,
            daemon=True,
        )
        worker.start()

        while True:
            frame = frame_queue.get()

            if frame is end_marker:
                break

            yield frame

        worker.join()

        if len(errors) > 0:
            raise errors[0]


def pixet_grpc_server(
    *,
    grpc_host: str,
    grpc_port: int,
    auto_connect: bool = True,
    logger: Optional[Any] = None,
    log_level: Optional[str] = None,
) -> None:
    if logger is None:
        raise ValueError("logger is required")

    ctrl = MiniPixGrpcCtrl(
        logger=logger,
        log_level=log_level,
    )
    server = None
    channel = None

    try:
        if auto_connect:
            connected = ctrl.connect()

            if not connected:
                raise RuntimeError("MiniPIX connection failed")

        server = create_grpc_server(
            ctrl_obj=ctrl,
            logger=logger,
            log_level=log_level,
            max_workers=10,
        )

        bind_addr = str(grpc_host) + ":" + str(grpc_port)
        ret = server.add_insecure_port(bind_addr)

        if ret == 0:
            raise RuntimeError("bind failed: " + bind_addr)

        server.start()
        logger.info("gRPC start OK: " + bind_addr)

        channel = grpc.insecure_channel(bind_addr)
        channel_ready_future(channel).result(timeout=2.0)
        logger.info("gRPC self-check OK")

        server.wait_for_termination()

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")

    finally:
        if channel is not None:
            channel.close()

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
