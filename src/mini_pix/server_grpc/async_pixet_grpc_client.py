from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional, Sequence, Tuple

import grpc
import numpy as np
import tifffile

from grpc_frame import AsyncGrpcClient
from grpc_frame import ctrl_pb2
from grpc_frame import ctrl_pb2_grpc
from grpc_frame.adapter import pack_args
from grpc_frame.adapter import pack_kwargs
from grpc_frame.adapter import unpack_result


class AsyncPixetGrpcClient(AsyncGrpcClient):
    """
    MiniPixCtrl の非同期 gRPC クライアント。

    通常測定:
        acquire_frames() / acquire_integral()
        サーバー側 MiniPixCtrl の測定結果全体を受信する。

    VIEW:
        stream_frames()
        各フレームを逐次受信する。

        stream_integral()
        Integral の最終積算フレームを1回だけ受信する。

    ローカル保存:
        name の拡張子が .tif/.tiff の場合は raw 数値配列を TIFF 保存する。
        .png の場合は表示用16 bit PNGとして保存する。
        サーバー側保存とは独立している。
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

        self._server_ip = server_ip
        self._server_port = int(server_port)
        self._stream_timeout_sec = effective_timeout_sec
        self._grpc_options = grpc_options

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
            struct.pack("!I", len(data))
            + chunk_type
            + data
            + struct.pack(
                "!I",
                zlib.crc32(chunk_type + data) & 0xFFFFFFFF,
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
            raise RuntimeError("PNG data must be a 2D array")

        values = array.astype(np.float64)
        minimum = float(np.min(values))
        maximum = float(np.max(values))

        if maximum > minimum:
            values = (values - minimum) / (maximum - minimum)
        else:
            values = np.zeros(values.shape, dtype=np.float64)

        values = np.clip(values, 0.0, 1.0)
        values = np.rint(values * 65535.0).astype(np.uint16)

        height = int(values.shape[0])
        width = int(values.shape[1])

        raw = bytearray()

        for row_index in range(height):
            raw.append(0)

            for column_index in range(width):
                raw.extend(
                    struct.pack(
                        "!H",
                        int(values[row_index, column_index]),
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
        png.extend(b"\x89PNG\r\n\x1a\n")
        png.extend(cls._make_png_chunk(b"IHDR", ihdr))
        png.extend(
            cls._make_png_chunk(
                b"IDAT",
                zlib.compress(bytes(raw), level=9),
            )
        )
        png.extend(cls._make_png_chunk(b"IEND", b""))

        path.write_bytes(bytes(png))

    @classmethod
    def _save_result_files(
        cls,
        result: Dict[str, Any],
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
                "local image name must end with .tif, .tiff, or .png"
            )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        frames = list(result.get("frames", []))

        for frame_index, frame in enumerate(frames):
            if len(frames) == 1:
                frame_path = target
            else:
                frame_path = (
                    target.parent
                    / (
                        target.stem
                        + "_"
                        + str(frame_index + 1).zfill(6)
                        + target.suffix
                    )
                )

            data = np.asarray(frame["data"])

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

    def _finish_acquisition(
        self,
        result: Dict[str, Any],
        name: Optional[str],
        save_local: bool,
        return_data: bool,
    ):
        if save_local:
            if name is None:
                raise ValueError(
                    "name is required when save_local=True"
                )

            self._save_result_files(
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
        *,
        name: Optional[str] = None,
        save_local: bool = False,
        return_data: bool = True,
        save_format: Optional[str] = None,
        save_path: Optional[str] = None,
    ):
        result = await self._grpc_acquire_frames(
            count,
            sec,
            callback=None,
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
        *,
        name: Optional[str] = None,
        save_local: bool = False,
        return_data: bool = True,
        save_format: Optional[str] = None,
        save_path: Optional[str] = None,
    ):
        result = await self._grpc_acquire_integral(
            count,
            sec,
            callback=None,
            save_format=save_format,
            save_path=save_path,
        )

        return self._finish_acquisition(
            result,
            name,
            save_local,
            return_data,
        )

    async def _stream_method(
        self,
        method_name: str,
        count: int,
        sec: float,
    ) -> AsyncIterator[Dict[str, Any]]:
        target = (
            str(self._server_ip)
            + ":"
            + str(self._server_port)
        )

        options = self._grpc_options

        if options is None:
            options = []

        channel = grpc.aio.insecure_channel(
            target,
            options=options,
        )

        try:
            stub = ctrl_pb2_grpc.ControlStub(channel)

            request = ctrl_pb2.DispatchRequest(
                method=method_name,
                args=pack_args(
                    (
                        count,
                        sec,
                    )
                ),
                kwargs=pack_kwargs({}),
            )

            call = stub.StreamCall(
                request,
                timeout=self._stream_timeout_sec,
            )

            async for response in call:
                if not response.ok:
                    raise RuntimeError(response.error)

                frame = unpack_result(response.result)

                if not isinstance(frame, dict):
                    raise RuntimeError(
                        "stream response is not a frame dict"
                    )

                yield frame

        finally:
            await channel.close()

    async def stream_frames(
        self,
        count: int,
        sec: float,
    ) -> AsyncIterator[Dict[str, Any]]:
        async for frame in self._stream_method(
            "stream_frames",
            count,
            sec,
        ):
            yield frame

    async def stream_integral(
        self,
        count: int,
        sec: float,
    ) -> AsyncIterator[Dict[str, Any]]:
        async for frame in self._stream_method(
            "stream_integral",
            count,
            sec,
        ):
            yield frame
