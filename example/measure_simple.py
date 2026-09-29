#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path

import asyncio
# from mini_pix.server_grpc import AsyncPixetGrpcClient
from mini_pix.server_grpc import DeviceProxy
from x_logger import XLogger

async def main() -> None:
    logger = XLogger(
        log_level="INFO",
        logger_name="MiniPixMeasurementClient",
    )

    # client = AsyncPixetGrpcClient("10.170.10.38", 50051)
    client = DeviceProxy(
        "mini_pix",
        server_ip="10.170.10.38",
        server_port=50051,
        set_timeout_sec=30.0,
        async_mode=True,
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR = Path("measurement_output")
    output_path = OUTPUT_DIR / f"minipix_{timestamp}.png"

    await client.connect()

    # Energy: TOT
    # Counting: COUNT
    # Time: TOA
    await client.set_mode_all("Energy")
    await client.set_threshold(5.0)  # keV
    # await client.set_threshold(6.0)  # keV
    await client.set_bias(150) # V
    await client.set_clock(9.66667) # MHz

    result = await client.simple_acq(
        1,  # FrameCount
        1.0,  # sec
        "example.png",  # output_path
        # name=str(output_path),
        # save_file=False,
        # save_local=True,
        # return_data=True,
    )

    frame_count = len(result.get("frames", []))
    logger.info(f"measurement complete: frames={frame_count}")
    logger.info(f"saved locally: {output_path.parent.resolve()}")

if __name__ == "__main__":
    asyncio.run(main())
