#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path

import asyncio
from mini_pix.server_grpc import AsyncPixetGrpcClient
# from mini_pix.server_grpc import DeviceProxy

# n# Detector settings
# nMODE = "TOT"
# n#THRESHOLD_KEV = 6.0
# nTHRESHOLD_KEV = 5.0
# n# BIAS_VOLT = 150.0
# nBIAS_VOLT = 150.0
# nCLOCK_MHZ = 9.66667
# n
# n# Measurement settings
# nFRAME_COUNT = 1
# n# EXPOSURE_SEC = 3.0
# nEXPOSURE_SEC = 0.1
# nOUTPUT_DIR = Path("measurement_output")

async def main() -> None:
    client = AsyncPixetGrpcClient("10.170.10.38", 50051)
    # client = DeviceProxy(
    #     "mini_pix",
    #     server_ip="10.170.10.38",
    #     server_port=50051,
    #     async_mode=True,
    # )
    await client.connect()

    # Energy: TOT
    # Counting: COUNT
    # Time: TOA
    await client.set_mode_all("Energy")
    await client.set_threshold(5.0)  # keV
    await client.set_bias(150) # V
    await client.set_clock(9.66667) # MHz
    await client.simple_acq(
        1,  # FrameCount
        1.0,  # sec
        "example.png",  # output_path
    )


if __name__ == "__main__":
    asyncio.run(main())
