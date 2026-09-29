#!/usr/bin/env python3
import asyncio

from mini_pix.server_grpc import AsyncPixetGrpcClient


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
