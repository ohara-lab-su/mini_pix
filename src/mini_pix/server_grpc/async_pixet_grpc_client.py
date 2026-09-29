from __future__ import annotations

import json
import re
import struct
import zlib
from pathlib import Path
from typing import Any, Optional, Sequence, Tuple

from grpc_frame import AsyncGrpcClient


class AsyncPixetGrpcClient(AsyncGrpcClient):
    def __init__(
        self,
        server_ip: str,
        server_port: int,
        timeout_sec: Optional[float] = None,
        logger: Optional[Any] = None,
        log_level: Optional[str] = None,
        grpc_options: Optional[Sequence[Tuple[str, Any]]] = None,
        set_timeout_sec: Optional[float] = None,
    ) -> None:
        if timeout_sec is not None and set_timeout_sec is not None:
            raise ValueError(
                "timeout_sec and set_timeout_sec cannot be specified together"
            )

        effective_timeout_sec = set_timeout_sec
        if timeout_sec is not None:
            effective_timeout_sec = timeout_sec

        super().__init__(
            server_ip=server_ip,
            server_port=server_port,
            timeout_sec=effective_timeout_sec,
            logger=logger,
            log_level=log_level,
            grpc_options=grpc_options,
        )

        self._grpc_simple_acq = self.simple_acq
        self.simple_acq = self._simple_acq_async

    @staticmethod
    def _format_file_name(value: str) -> str:
        text = re.sub(r"[^0-9A-Za-z._-]+", "_", value).strip("_")
        if text:
            return text
        return "frame"

    @staticmethod
    def _make_png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        return (
            struct.pack("!I", len(data))
            + chunk_type
            + data
            + struct.pack("!I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        )

    @classmethod
    def _write_png(
        cls,
        path: Path,
        width: int,
        height: int,
        data: list,
    ) -> None:
        pixels = [int(v) for v in data]
        if len(pixels) != width * height:
            raise RuntimeError(
                f"pixel count mismatch: expected={width * height}, actual={len(pixels)}"
            )

        max_value = 0
        if pixels:
            max_value = max(pixels)

        scale = 1.0
        if max_value > 0:
            scale = 65535.0 / float(max_value)

        raw = bytearray()
        for row_index in range(height):
            raw.append(0)
            row = pixels[row_index * width : (row_index + 1) * width]
            for value in row:
                scaled = int(max(0, min(65535, round(value * scale))))
                raw.extend(struct.pack("!H", scaled))

        ihdr = struct.pack("!IIBBBBB", width, height, 16, 0, 0, 0, 0)
        idat = zlib.compress(bytes(raw), level=9)

        png = bytearray()
        png.extend(b"\x89PNG\r\n\x1a\n")
        png.extend(cls._make_png_chunk(b"IHDR", ihdr))
        png.extend(cls._make_png_chunk(b"IDAT", idat))
        png.extend(cls._make_png_chunk(b"IEND", b""))
        path.write_bytes(bytes(png))

    @classmethod
    def _save_result_files(
        cls,
        result: dict,
        name: str,
    ) -> None:
        target = Path(name)
        parent = Path(".")
        if str(target.parent) not in ("", "."):
            parent = target.parent
        parent.mkdir(parents=True, exist_ok=True)

        stem = target.name
        if target.suffix:
            stem = target.stem
        frames = list(result.get("frames", []))

        meta = {
            "rc": result.get("rc"),
            "saved_file": result.get("saved_file", ""),
            "frame_count": len(frames),
            "frames": [
                {
                    "name": frame.get("name"),
                    "width": frame.get("width"),
                    "height": frame.get("height"),
                    "subframe_count": len(frame.get("subframes", [])),
                }
                for frame in frames
            ],
        }
        (parent / f"{stem}_meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if len(frames) == 1:
            frame = frames[0]
            cls._write_png(
                parent / f"{stem}.png",
                int(frame["width"]),
                int(frame["height"]),
                frame["data"],
            )
            for sub_index, subframe in enumerate(frame.get("subframes", [])):
                subframe_name = cls._format_file_name(
                    str(subframe.get("name", "subframe"))
                )
                cls._write_png(
                    parent / f"{stem}_sub{sub_index}_{subframe_name}.png",
                    int(subframe["width"]),
                    int(subframe["height"]),
                    subframe["data"],
                )
            return

        for frame_index, frame in enumerate(frames):
            frame_name = cls._format_file_name(str(frame.get("name", "frame")))
            cls._write_png(
                parent / f"{stem}_frame{frame_index}_{frame_name}.png",
                int(frame["width"]),
                int(frame["height"]),
                frame["data"],
            )
            for sub_index, subframe in enumerate(frame.get("subframes", [])):
                subframe_name = cls._format_file_name(
                    str(subframe.get("name", "subframe"))
                )
                cls._write_png(
                    parent
                    / f"{stem}_frame{frame_index}_sub{sub_index}_{subframe_name}.png",
                    int(subframe["width"]),
                    int(subframe["height"]),
                    subframe["data"],
                )

    def _finish_simple_acq(
        self,
        result: dict,
        name: str,
        save_local: bool,
        return_data: bool,
    ):
        if save_local:
            self._save_result_files(result, name)
        if return_data:
            return result
        return result["rc"]

    async def _simple_acq_async(
        self,
        count: int,
        sec: float,
        name: str = "example.png",
        *,
        save_file: bool = False,
        save_local: bool = True,
        return_data: bool = False,
    ):
        result = await self._grpc_simple_acq(
            count,
            sec,
            name=name,
            save_file=save_file,
            return_data=True,
        )
        return self._finish_simple_acq(result, name, save_local, return_data)


if __name__ == "__main__":
    import asyncio

    from mini_pix.config import Config
    from x_logger import XLogger

    async def main() -> None:
        config = Config("mini_pix.yaml")

        logger_ = XLogger(
            log_level=config.LOGGER_LEVEL,
            logger_name=config.CLIENT_LOGGER_NAME,
        )

        client = AsyncPixetGrpcClient(
            server_ip=config.SERVER_IP,
            server_port=config.SERVER_PORT,
            set_timeout_sec=config.TIMEOUT,
            logger=logger_,
            log_level=config.LOGGER_LEVEL,
        )

        try:
            await client.connect()
            await client.set_mode_all("TOT")
            await client.set_threshold(1000)
            await client.simple_acq(1, 1.0, "example.png")
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    asyncio.run(main())
