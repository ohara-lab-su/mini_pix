from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Any, Optional, Sequence, Tuple

import numpy as np
import tifffile

from grpc_frame import AsyncGrpcClient


class AsyncPixetGrpcClient(AsyncGrpcClient):
    """
    MiniPIX 用 AsyncGrpcClient。

    CTRL由来の acquire_frames/acquire_integral をローカル保存対応で上書きする。
    TIFF は raw 数値配列をそのまま保存する。
    PNG は表示用16 bit grayscaleへ変換して保存する。
    """

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

        self._grpc_acquire_frames = self.acquire_frames
        self._grpc_acquire_integral = self.acquire_integral

        self.acquire_frames = self._acquire_frames_async
        self.acquire_integral = self._acquire_integral_async

    @staticmethod
    def _make_png_chunk(
        chunk_type: bytes,
        data: bytes,
    ) -> bytes:
        return (
            struct.pack(
                "!I",
                len(data),
            )
            + chunk_type
            + data
            + struct.pack(
                "!I",
                zlib.crc32(
                    chunk_type + data
                )
                & 0xFFFFFFFF,
            )
        )

    @classmethod
    def _write_png(
        cls,
        path: Path,
        data,
    ) -> None:
        array = np.asarray(data)

        if array.ndim != 2:
            raise RuntimeError(
                "PNG data must be a 2D array"
            )

        values = array.astype(
            np.float64
        )

        minimum = float(
            np.min(values)
        )
        maximum = float(
            np.max(values)
        )

        if maximum > minimum:
            values = (
                values - minimum
            ) / (
                maximum - minimum
            )
        else:
            values = np.zeros(
                values.shape,
                dtype=np.float64,
            )

        values = np.clip(
            values,
            0.0,
            1.0,
        )

        values = np.rint(
            values * 65535.0
        ).astype(
            np.uint16
        )

        height = int(
            values.shape[0]
        )
        width = int(
            values.shape[1]
        )

        raw = bytearray()

        for row_index in range(
            height
        ):
            raw.append(0)

            for column_index in range(
                width
            ):
                raw.extend(
                    struct.pack(
                        "!H",
                        int(
                            values[
                                row_index,
                                column_index,
                            ]
                        ),
                    )
                )

        ihdr = struct.pack(
            "!IIBBBBB",
            width,
            height,
            16,
            0,
            0,
            0,
            0,
        )

        png = bytearray()
        png.extend(
            b"\x89PNG\r\n\x1a\n"
        )
        png.extend(
            cls._make_png_chunk(
                b"IHDR",
                ihdr,
            )
        )
        png.extend(
            cls._make_png_chunk(
                b"IDAT",
                zlib.compress(
                    bytes(raw),
                    level=9,
                ),
            )
        )
        png.extend(
            cls._make_png_chunk(
                b"IEND",
                b"",
            )
        )

        path.write_bytes(
            bytes(png)
        )

    @classmethod
    def _save_result_files(
        cls,
        result: dict,
        name: str,
    ) -> None:
        target = Path(name)
        suffix = target.suffix.lower()

        if suffix not in {
            ".tif",
            ".tiff",
            ".png",
        }:
            raise ValueError(
                "name must end with .tif, .tiff, or .png"
            )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        frames = list(
            result.get(
                "frames",
                [],
            )
        )

        for frame_index, frame in enumerate(
            frames
        ):
            frame_path = target

            if len(frames) > 1:
                frame_path = (
                    target.parent
                    / (
                        target.stem
                        + "_"
                        + str(
                            frame_index + 1
                        ).zfill(6)
                        + target.suffix
                    )
                )

            data = np.asarray(
                frame["data"]
            )

            if suffix in {
                ".tif",
                ".tiff",
            }:
                tifffile.imwrite(
                    str(frame_path),
                    data,
                )
            else:
                cls._write_png(
                    frame_path,
                    data,
                )

    @classmethod
    def _finish_acquisition(
        cls,
        result: dict,
        name: str,
        save_local: bool,
        return_data: bool,
    ):
        if save_local:
            cls._save_result_files(
                result,
                name,
            )

        if return_data:
            return result

        return result["rc"]

    async def _acquire_frames_async(
        self,
        count: int,
        sec: float,
        name: str = "frame.tiff",
        *,
        save_local: bool = True,
        return_data: bool = False,
        save_format=None,
        save_path=None,
    ):
        result = await self._grpc_acquire_frames(
            count,
            sec,
            save_format=save_format,
            save_path=save_path,
        )

        return self._finish_acquisition(
            result,
            name,
            save_local,
            return_data,
        )

    async def _acquire_integral_async(
        self,
        count: int,
        sec: float,
        name: str = "integral.tiff",
        *,
        save_local: bool = True,
        return_data: bool = False,
        save_format=None,
        save_path=None,
    ):
        result = await self._grpc_acquire_integral(
            count,
            sec,
            save_format=save_format,
            save_path=save_path,
        )

        return self._finish_acquisition(
            result,
            name,
            save_local,
            return_data,
        )
