#!/usr/bin/env python3
"""Run one MiniPIX measurement through the gRPC device server."""

import asyncio
from datetime import datetime
from pathlib import Path

from mini_pix.server_grpc import AsyncPixetGrpcClient
from x_logger import XLogger


# gRPC server
#SERVER_IP = "127.0.0.1"
SERVER_IP = "10.170.10.38"
SERVER_PORT = 50051
TIMEOUT_SEC = 30.0

# Detector settings
MODE = "TOT"
#THRESHOLD_KEV = 6.0
THRESHOLD_KEV = 5.0
# BIAS_VOLT = 150.0
BIAS_VOLT = 150.0
CLOCK_MHZ = 9.66667

# Measurement settings
FRAME_COUNT = 1
# EXPOSURE_SEC = 3.0
EXPOSURE_SEC = 0.1
OUTPUT_DIR = Path("measurement_output")


async def main() -> None:
    logger = XLogger(
        log_level="INFO",
        logger_name="MiniPixMeasurementClient",
    )
    client = AsyncPixetGrpcClient(
        server_ip=SERVER_IP,
        server_port=SERVER_PORT,
        timeout_sec=TIMEOUT_SEC,
        logger=logger,
        log_level="INFO",
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"minipix_{timestamp}.png"

    try:
        await client.connect()
        await client.set_mode_all(MODE)
        await client.set_threshold(THRESHOLD_KEV)
        await client.set_bias(BIAS_VOLT)
        await client.set_clock(CLOCK_MHZ)

        result = await client.simple_acq(
            count=FRAME_COUNT,
            sec=EXPOSURE_SEC,
            name=str(output_path),
            save_file=False,
            save_local=True,
            return_data=True,
        )

        frame_count = len(result.get("frames", []))
        logger.info(f"measurement complete: frames={frame_count}")
        logger.info(f"saved locally: {output_path.parent.resolve()}")
    finally:
        try:
            await client.disconnect()
        except Exception as exc:
            logger.warning(f"disconnect failed: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
