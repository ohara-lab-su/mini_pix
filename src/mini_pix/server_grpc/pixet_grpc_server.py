#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Dict, Optional

import grpc
from grpc import channel_ready_future

from grpc_frame.grpc_server import create_grpc_server
from mini_pix.config import Config
from mini_pix.pixet_ctrl import MiniPixCtrl
from x_logger import XLogger



class MiniPixGrpcService:
    """
    MiniPixCtrl を grpc_frame へ公開するサービス層。

    MiniPixCtrl は完全ローカル制御クラスのまま変更しない。
    grpc_frame の EventBus は _set_event_bus() から注入される。

    Frames:
        MiniPixCtrl の acquisition callback ごとに minipix.frame へ publish。

    Integral:
        PIXet の doSimpleIntegralAcquisition() 完了後の最終積算フレームだけを
        minipix.frame へ1回 publish。
    """

    def __init__(
        self,
        ctrl: Optional[MiniPixCtrl] = None,
        topic_name: str = "minipix.frame",
        logger: Optional[Any] = None,
        log_level: Optional[str] = None,
    ):
        if logger is None:
            raise ValueError("logger is required")

        self._logger = logger
        self._topic_name = str(topic_name)
        self._event_bus = None

        self._ctrl = ctrl

        if self._ctrl is None:
            self._ctrl = MiniPixCtrl(
                logger=logger,
                log_level=log_level,
            )

    def _set_event_bus(
        self,
        event_bus,
    ) -> None:
        """grpc_frame から EventBus を設定する。"""
        self._event_bus = event_bus

    def connect(self) -> bool:
        return self._ctrl.connect()

    def disconnect(self):
        return self._ctrl.disconnect()

    def set_mode_all(
        self,
        mode: str,
    ) -> bool:
        return self._ctrl.set_mode_all(mode)

    def set_threshold(
        self,
        threshold_kev: float,
    ) -> bool:
        return self._ctrl.set_threshold(
            threshold_kev
        )

    def set_clock(
        self,
        clock_mhz: float,
    ) -> bool:
        return self._ctrl.set_clock(
            clock_mhz
        )

    def set_bias(
        self,
        bias_v: float,
    ) -> bool:
        return self._ctrl.set_bias(
            bias_v
        )

    def clear_frames(self):
        return self._ctrl.clear_frames()

    def get_frame_count(self) -> int:
        return self._ctrl.get_frame_count()

    def get_frame(
        self,
        index: int,
    ) -> Dict[str, Any]:
        return self._ctrl.get_frame(index)

    def get_frames(self):
        return self._ctrl.get_frames()

    def get_current_frame(self):
        return self._ctrl.get_current_frame()

    def get_acq_frame_count(self) -> int:
        return self._ctrl.get_acq_frame_count()

    def get_acq_frames(
        self,
        idx=None,
    ):
        return self._ctrl.get_acq_frames(idx)

    def _publish_frame(
        self,
        frame: Dict[str, Any],
    ) -> None:
        if self._event_bus is None:
            return

        self._event_bus.publish(
            self._topic_name,
            frame,
            source="minipix_grpc_service",
        )

    def acquire(
        self,
        count: int,
        sec: float,
        acquisition_type: str = "frames",
        save_format=None,
        save_path=None,
    ):
        acquisition = str(
            acquisition_type
        ).strip().lower()

        if acquisition == "frames":
            return self.acquire_frames(
                count=count,
                sec=sec,
                save_format=save_format,
                save_path=save_path,
            )

        if acquisition == "integral":
            return self.acquire_integral(
                count=count,
                sec=sec,
                save_format=save_format,
                save_path=save_path,
            )

        raise ValueError(
            'acquisition_type must be "frames" or "integral"'
        )

    def acquire_frames(
        self,
        count: int,
        sec: float,
        save_format=None,
        save_path=None,
    ):
        return self._ctrl.acquire_frames(
            count=count,
            sec=sec,
            callback=self._publish_frame,
            save_format=save_format,
            save_path=save_path,
        )

    def acquire_integral(
        self,
        count: int,
        sec: float,
        save_format=None,
        save_path=None,
    ):
        return self._ctrl.acquire_integral(
            count=count,
            sec=sec,
            callback=self._publish_frame,
            save_format=save_format,
            save_path=save_path,
        )

    def stop(self):
        return self._ctrl.stop()

    def is_running(self) -> bool:
        return self._ctrl.is_running()

    def is_aborting(self) -> bool:
        return self._ctrl.is_aborting()

    def state(self):
        return self._ctrl.state()

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

    service = MiniPixGrpcService(
        logger=logger,
        log_level=log_level,
    )

    server = None
    self_check_channel = None

    try:
        if auto_connect:
            connected = service.connect()

            if not connected:
                raise RuntimeError(
                    "MiniPIX connection failed"
                )

        server = create_grpc_server(
            ctrl_obj=service,
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

        server.start()

        logger.info(
            "gRPC start OK: "
            + bind_addr
        )

        self_check_channel = grpc.insecure_channel(
            bind_addr
        )

        channel_ready_future(
            self_check_channel
        ).result(
            timeout=2.0
        )

        logger.info(
            "gRPC self-check OK"
        )

        server.wait_for_termination()

    except KeyboardInterrupt:
        logger.info(
            "KeyboardInterrupt"
        )

    finally:
        if self_check_channel is not None:
            self_check_channel.close()

        if server is not None:
            server.stop(
                grace=None
            )

        try:
            service.disconnect()
        except Exception:
            pass

        logger.info(
            "gRPC server stopped"
        )


pixet_server = pixet_grpc_server


if __name__ == "__main__":
    config = Config(
        "mini_pix.yaml"
    )

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
