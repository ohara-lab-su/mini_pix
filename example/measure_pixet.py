#!/usr/bin/env python3
import asyncio
from mini_pix.server_grpc import AsyncPixetGrpcClient
# from mini_pix.server_grpc import DeviceProxy


async def main() -> None:
    client = AsyncPixetGrpcClient("10.170.10.38", 50051)
    # client = DeviceProxy(
    #     "mini_pix",
    #     server_ip="10.170.10.38",
    #     server_port=50051,
    #     async_mode=True,
    # )

    await client.set_mode_all("TOT")
    await client.set_threshold(1000)
    await client.simple_acq(1, 1.0, "example.png")


if __name__ == "__main__":
    asyncio.run(main())
