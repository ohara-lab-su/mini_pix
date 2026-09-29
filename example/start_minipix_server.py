#!/usr/bin/env python3
"""Start the MiniPIX gRPC device server."""

from mini_pix.server_grpc import pixet_grpc_server


GRPC_HOST = "0.0.0.0"
GRPC_PORT = 50051
AUTO_CONNECT = True
LOG_LEVEL = "INFO"


def main() -> None:
    pixet_grpc_server(
        grpc_host=GRPC_HOST,
        grpc_port=GRPC_PORT,
        auto_connect=AUTO_CONNECT,
        log_level=LOG_LEVEL,
    )


if __name__ == "__main__":
    main()