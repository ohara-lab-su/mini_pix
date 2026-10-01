#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mini_pix.server_grpc の pyi 生成用 make_pyi.py である。

このスクリプトは gRPC client の pyi のみを生成する。
現状の二次元検出器制御は flat な server_grpc 構造であるため、clients/routers の
サブディレクトリは前提にしない。

生成対象:
・ sync_pixet_grpc_client.pyi
・ async_pixet_grpc_client.pyi

方針:
・ gRPC client pyi は grpc_frame.make_pyi.generate_client_pyi を使う。
・ __init__.py / __init__.pyi は公開 API の手書きファイルであり、生成・削除・上書きしない。
・ pixet_ctrl.py は制御本体であり、__init__.py には import しない。
・ client 側で実装されている acquire_frames/acquire_integral の上書きと補助メソッドは、生成 pyi 後に補正する。
"""

import re
from pathlib import Path

import grpc_frame
from grpc_frame.make_pyi import generate_client_pyi



SYNC_CLIENT_PY = "sync_pixet_grpc_client.py"
ASYNC_CLIENT_PY = "async_pixet_grpc_client.py"
CTRL_PY = "../pixet_ctrl.py"

SYNC_CLIENT_PYI = "sync_pixet_grpc_client.pyi"
ASYNC_CLIENT_PYI = "async_pixet_grpc_client.pyi"

CTRL_CLASS = "MiniPixCtrl"
SYNC_CLIENT_CLASS = "SyncPixetGrpcClient"
ASYNC_CLIENT_CLASS = "AsyncPixetGrpcClient"



def _read_lines(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def _write_lines(filename, lines):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _ensure_import(lines, import_line):
    """import_line を最初の class 定義より前に一度だけ挿入する。"""
    if any(line.strip() == import_line.strip() for line in lines):
        return lines

    out = []
    inserted = False
    for line in lines:
        if not inserted and line.startswith("class "):
            out.append(import_line)
            inserted = True
        out.append(line)

    if not inserted:
        out.append(import_line)

    return out


def _replace_class_base(lines, class_name, base_class_name):
    """生成 pyi の class 定義を実装側の継承関係に合わせる。"""
    pattern = re.compile(
        r"^(class\s+" + re.escape(class_name) + r")\s*(?:\([^)]*\))?:\s*$"
    )
    target = "class {}({}):".format(class_name, base_class_name)

    out = []
    for line in lines:
        if pattern.match(line):
            out.append(target)
        else:
            out.append(line)
    return out


def _find_class_block(lines, class_name):
    pattern = re.compile(r"^class\s+" + re.escape(class_name) + r"(?:\(|:)")
    start = None

    for index, line in enumerate(lines):
        if pattern.match(line):
            start = index
            break

    if start is None:
        raise RuntimeError("class not found in generated pyi: {}".format(class_name))

    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line and not line.startswith((" ", "\t", "#")):
            end = index
            break

    return start, end


def _member_signature_key(line):
    stripped = line.strip()
    if stripped.startswith("async def "):
        return stripped.split("(", 1)[0]
    if stripped.startswith("def "):
        return stripped.split("(", 1)[0]
    if stripped.startswith("@"):
        return stripped
    return stripped


def _remove_class_members(lines, class_name, member_names):
    """生成 pyi にある ctrl 由来の同名メソッドを、client 実装用に差し替える。"""
    start, end = _find_class_block(lines, class_name)
    out = list(lines[:start + 1])
    index = start + 1

    def is_def(line):
        stripped = line.strip()
        return stripped.startswith("def ") or stripped.startswith("async def ")

    while index < end:
        line = lines[index]
        stripped = line.strip()
        remove = False
        for name in member_names:
            if stripped.startswith("def {}(".format(name)):
                remove = True
                break
            if stripped.startswith("async def {}(".format(name)):
                remove = True
                break

        if not remove:
            out.append(line)
            index += 1
            continue

        # 直前に付いた overload/comment も消すため、out 側を少し戻す。
        while out and out[-1].strip().startswith(("@overload", "#")):
            out.pop()

        index += 1
        while index < end:
            next_line = lines[index]
            if is_def(next_line) or next_line.strip().startswith("@overload"):
                break
            if next_line and not next_line.startswith((" ", "\t")):
                break
            index += 1

    out.extend(lines[end:])
    return out


def _ensure_class_members(lines, class_name, member_lines):
    """API spec 外または client 側で上書きされたメソッドを class ブロック内へ追加する。"""
    if not member_lines:
        return lines

    start, end = _find_class_block(lines, class_name)
    class_lines = lines[start:end]
    existing_keys = set(_member_signature_key(line) for line in class_lines)

    missing = []
    for line in member_lines:
        key = _member_signature_key(line)
        if key in existing_keys:
            continue
        missing.append(line)

    if not missing:
        return lines

    out = list(lines[:end])
    if out and out[-1].strip() != "":
        out.append("")
    out.extend(missing)
    out.extend(lines[end:])
    return out


def _patch_client_pyi(filename, base_import_line, class_name, base_class_name, extra_lines):
    lines = _read_lines(filename)
    lines = _ensure_import(lines, "from typing import Any")
    lines = _ensure_import(lines, base_import_line)
    lines = _replace_class_base(lines, class_name, base_class_name)
    lines = _remove_class_members(lines, class_name, ["acquire_frames", "acquire_integral"])
    lines = _ensure_class_members(lines, class_name, extra_lines)
    _write_lines(filename, lines)


def make_client_pyi():
    base = Path(__file__).resolve().parent
    grpc_base = Path(grpc_frame.__file__).resolve().parent

    generate_client_pyi(
        client_py=base / SYNC_CLIENT_PY,
        client_class=SYNC_CLIENT_CLASS,
        ctrl_py=(base / CTRL_PY).resolve(),
        ctrl_class=CTRL_CLASS,
        base_py=grpc_base / "grpc_client.py",
        base_class="SyncGrpcClient",
        out_path=base / SYNC_CLIENT_PYI,
        ctrl_async=False,
    )
    _patch_client_pyi(
        filename=base / SYNC_CLIENT_PYI,
        base_import_line=(
            "from mini_pix.server_grpc.async_pixet_grpc_client import "
            "AsyncPixetGrpcClient"
        ),
        class_name=SYNC_CLIENT_CLASS,
        base_class_name="AsyncPixetGrpcClient",
        extra_lines=[
            "    # --- methods defined in .py, not in ctrl-derived pyi ---",
            "    def _acquire_frames_sync(self, count: int, sec: float, name: str = ..., *, save_local: bool = ..., return_data: bool = ..., save_format: Any = ..., save_path: Any = ...) -> Any: ...",
            "    def _acquire_integral_sync(self, count: int, sec: float, name: str = ..., *, save_local: bool = ..., return_data: bool = ..., save_format: Any = ..., save_path: Any = ...) -> Any: ...",
            "    def acquire_frames(self, count: int, sec: float, name: str = ..., *, save_local: bool = ..., return_data: bool = ..., save_format: Any = ..., save_path: Any = ...) -> Any: ...",
            "    def acquire_integral(self, count: int, sec: float, name: str = ..., *, save_local: bool = ..., return_data: bool = ..., save_format: Any = ..., save_path: Any = ...) -> Any: ...",
        ],
    )

    generate_client_pyi(
        client_py=base / ASYNC_CLIENT_PY,
        client_class=ASYNC_CLIENT_CLASS,
        ctrl_py=(base / CTRL_PY).resolve(),
        ctrl_class=CTRL_CLASS,
        base_py=grpc_base / "grpc_client.py",
        base_class="AsyncGrpcClient",
        out_path=base / ASYNC_CLIENT_PYI,
        ctrl_async=True,
    )
    _patch_client_pyi(
        filename=base / ASYNC_CLIENT_PYI,
        base_import_line="from grpc_frame import AsyncGrpcClient",
        class_name=ASYNC_CLIENT_CLASS,
        base_class_name="AsyncGrpcClient",
        extra_lines=[
            "    # --- methods defined in .py, not in ctrl-derived pyi ---",
            "    @staticmethod",
            "    def _make_png_chunk(chunk_type: bytes, data: bytes) -> bytes: ...",
            "    @classmethod",
            "    def _write_png(cls, path: Any, data: Any) -> None: ...",
            "    @classmethod",
            "    def _save_result_files(cls, result: dict, name: str) -> None: ...",
            "    @classmethod",
            "    def _finish_acquisition(cls, result: dict, name: str, save_local: bool, return_data: bool) -> Any: ...",
            "    async def _acquire_frames_async(self, count: int, sec: float, name: str = ..., *, save_local: bool = ..., return_data: bool = ..., save_format: Any = ..., save_path: Any = ...) -> Any: ...",
            "    async def _acquire_integral_async(self, count: int, sec: float, name: str = ..., *, save_local: bool = ..., return_data: bool = ..., save_format: Any = ..., save_path: Any = ...) -> Any: ...",
            "    async def acquire_frames(self, count: int, sec: float, name: str = ..., *, save_local: bool = ..., return_data: bool = ..., save_format: Any = ..., save_path: Any = ...) -> Any: ...",
            "    async def acquire_integral(self, count: int, sec: float, name: str = ..., *, save_local: bool = ..., return_data: bool = ..., save_format: Any = ..., save_path: Any = ...) -> Any: ...",
        ],
    )



def main():
    make_client_pyi()


if __name__ == "__main__":
    main()
