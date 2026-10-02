#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from mini_pix.config import Config
from mini_pix.server_grpc import pixet_grpc_server
from x_logger import XLogger

import grpc_frame.ctrl_pb2_grpc

print(grpc_frame.ctrl_pb2_grpc.__file__)


if __name__ == "__main__":
    config = Config("mini_pix.yaml")

    AUTO_CONNECT = True

    logger = XLogger(
        log_level=config.LOGGER_LEVEL,
        logger_name=config.SERVER_LOGGER_NAME,
    )

    print(config.SERVER_IP)
    print(config.SERVER_PORT)
    print(AUTO_CONNECT)
    print(logger)
    print(config.LOGGER_LEVEL)

    pixet_grpc_server(
        grpc_host=config.SERVER_IP,
        grpc_port=config.SERVER_PORT,
        auto_connect=AUTO_CONNECT,
        logger=logger,
        log_level=config.LOGGER_LEVEL,
    )
