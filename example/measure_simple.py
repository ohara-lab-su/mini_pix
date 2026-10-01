#!/usr/bin/env python3
import asyncio
from datetime import datetime
from pathlib import Path

from mini_pix.config import Config
from mini_pix.server_grpc import DeviceProxy
from x_logger import XLogger


SAVE_FORMAT = "TIFF"
OUTPUT_DIR = Path("measurement_output")


async def main() -> None:
    config = Config("mini_pix.yaml")

    logger = XLogger(
        log_level=config.LOGGER_LEVEL,
        logger_name=config.CLIENT_LOGGER_NAME,
    )

    client = DeviceProxy(
        "mini_pix",
        server_ip=config.SERVER_IP,
        server_port=config.SERVER_PORT,
        set_timeout_sec=config.TIMEOUT,
        async_mode=config.ASYNC_MODE,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if SAVE_FORMAT == "TIFF":
        output_path = OUTPUT_DIR / ("minipix_" + timestamp + ".tiff")
    elif SAVE_FORMAT == "PNG":
        output_path = OUTPUT_DIR / ("minipix_" + timestamp + ".png")
    else:
        raise ValueError('SAVE_FORMAT must be "TIFF" or "PNG"')

    await client.connect()

    try:
        await client.set_mode_all("Counting")
        await client.set_threshold(5.0)
        await client.set_bias(150)
        await client.set_clock(9.66667)

        result = await client.acquire_frames(
            1,
            1.0,
            name=str(output_path),
            save_local=True,
            return_data=True,
        )

        logger.info(
            "measurement complete: frame_count="
            + str(result["frame_count"])
        )
        logger.info(
            "saved locally: "
            + str(output_path.resolve())
        )

    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
