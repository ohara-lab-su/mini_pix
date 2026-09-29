#!/usr/bin/env python3
"""Run one MiniPIX measurement through the gRPC device server."""

import asyncio
from datetime import datetime
from pathlib import Path

from mini_pix.server_grpc import AsyncPixetGrpcClient
from x_logger import XLogger


# gRPC server
SERVER_IP = "127.0.0.1"
SERVER_PORT = 50051
TIMEOUT_SEC = 30.0

# Detector settings
MODE = "TOT"
THRESHOLD_KEV = 6.0
BIAS_VOLT = 150.0
CLOCK_MHZ = 9.66667

# Measurement settings
FRAME_COUNT = 1
EXPOSURE_SEC = 3.0
OUTPUT_DIR = Path("measurement_output")


async def main() -> None:
    #client = AsyncPixetGrpcClient("127.0.0.1", 50051)
    client = AsyncPixetGrpcClient("10.170.10.38", 50051)

    try:
        await client.connect()
        await client.set_mode_all("TOT")
        await client.set_threshold(1000)
        await client.simple_acq(1, 1.0, "example.png")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
