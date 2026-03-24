#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import pathlib

import grpc_frame
from grpc_frame.make_pyi import generate_client_pyi


def main() -> None:
    base = pathlib.Path(__file__).resolve().parent
    grpc_base = pathlib.Path(grpc_frame.__file__).resolve().parent

    generate_client_pyi(
        client_py=base / "pixet_grpc_client.py",
        client_class="PixetGrpcClient",
        ctrl_py=(base / "../pixet_ctrl.py").resolve(),
        ctrl_class="MiniPixCtrl",
        base_py=grpc_base / "grpc_client.py",
        base_class="GrpcClient",
        out_path=base / "pixet_grpc_client.pyi",
        ctrl_async=False,
    )

    generate_client_pyi(
        client_py=base / "async_pixet_grpc_client.py",
        client_class="AsyncPixetGrpcClient",
        ctrl_py=(base / "../pixet_ctrl.py").resolve(),
        ctrl_class="MiniPixCtrl",
        base_py=grpc_base / "grpc_client.py",
        base_class="GrpcClient",
        out_path=base / "async_pixet_grpc_client.pyi",
        ctrl_async=True,
    )


if __name__ == "__main__":
    main()
