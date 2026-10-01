#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path

import asyncio

from mini_pix.config import Config
from mini_pix.server_grpc import DeviceProxy
from x_logger import XLogger


async def main() -> None:
    config = Config(
        "mini_pix.yaml"
    )

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

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )
    output_dir = Path(
        "measurement_output"
    )

    # TIFF: raw detector data
    output_path = output_dir / (
        "minipix_"
        + timestamp
        + ".tiff"
    )

    # PNG: display image
    # output_path = output_dir / (
    #     "minipix_"
    #     + timestamp
    #     + ".png"
    # )

    await client.connect()

    try:
        await client.set_mode_all(
            "Counting"
        )
        await client.set_threshold(
            5.0
        )
        await client.set_bias(
            150
        )
        await client.set_clock(
            9.66667
        )

        await client.acquire_frames(
            1,
            1.0,
            name=str(output_path),
            save_local=True,
            return_data=False,
        )

        logger.info(
            "saved locally: "
            + str(
                output_path.resolve()
            )
        )

    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(
        main()
    )
