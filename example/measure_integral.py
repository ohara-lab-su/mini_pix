#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path

import asyncio
# from mini_pix.server_grpc import AsyncPixetGrpcClient
from mini_pix.config import Config
from mini_pix.server_grpc import DeviceProxy
from x_logger import XLogger

async def main() -> None:
    config = Config("mini_pix.yaml")

    logger = XLogger(
        log_level=config.LOGGER_LEVEL,
        logger_name=config.CLIENT_LOGGER_NAME,
    )

    # client = AsyncPixetGrpcClient("10.170.10.38", 50051)
    client = DeviceProxy(
        "mini_pix",
        server_ip=config.SERVER_IP,
        server_port=config.SERVER_PORT,
        set_timeout_sec=config.TIMEOUT,
        async_mode=config.ASYNC_MODE,
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR = Path("measurement_output")
    output_path = OUTPUT_DIR / f"minipix_integral_{timestamp}.png"

    await client.connect()

    # Energy: TOT
    # Counting: COUNT
    # Time: TOA
    await client.set_mode_all("Energy")
    await client.set_threshold(5.0)  # keV
    # await client.set_threshold(6.0)  # keV
    await client.set_bias(150) # V
    await client.set_clock(9.66667) # MHz

    result = await client.simple_int_acq(
        1,  # FrameCount
        1.0,  # sec
        "example.png",  # output_path
        # name=str(output_path),
        # save_file=False,
        # save_local=True,
        # return_data=True,
    )

    frame_count = len(result.get("frames", []))
    logger.info(f"integral measurement complete: frames={frame_count}")
    logger.info(f"saved locally: {output_path.parent.resolve()}")

if __name__ == "__main__":
    asyncio.run(main())
