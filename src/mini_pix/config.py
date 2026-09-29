"""

Kengo NAKADA:
https://github.com/shimane-dev, https://github.com/kengo-nakada
kengo.nakada@mat.shimane-u.ac.jp, kengo.nakada@gmail.com
"""

import os
import yaml
from typing import Union
from pathlib import Path
import inspect


class Config:
    # --- mini-pix server / client
    SERVER_IP = "10.170.10.38"
    SERVER_PORT = 50051
    TIMEOUT = 30.0
    ASYNC_MODE = True
    CLIENT_LOGGER_NAME = "mini_pix_client"
    SERVER_LOGGER_NAME = "mini_pix_server"
    LOGGER_LEVEL = "debug"

    def __init__(self, yaml_path=None):
        # インスタンスで使いたいときだけ、ここで個別設定
        if yaml_path:
            self._load_yaml(yaml_path=yaml_path, depth=3)

    @classmethod
    def load_yaml(
        cls,
        yaml_path,
    ):
        """クラスとして使う"""
        # if yaml_path is None:
        #     yaml_path = os.environ.get("MINI_PIX_CONFIG_YAML")
        #     if yaml_path is None:
        #         return

        # 新しいパス解決ロジックを使用
        # resolved_path = yaml_path
        resolved_path = cls._resolve_path(yaml_path=yaml_path, depth=2)
        with open(resolved_path, "r") as f:
            data = yaml.safe_load(f)

        for k, v in data.items():
            if hasattr(cls, k):
                setattr(cls, k, v)
            else:
                print("NO SUCH VAR:", k)

    def _load_yaml(
        self,
        *,
        yaml_path,
        depth: int,
    ):
        """コンストラクタから呼び出す"""
        # インスタンス用：インスタンスdictにのみ上書き
        print("load_yaml:", yaml_path)
        if yaml_path is None:
            yaml_path = os.environ.get("MINI_PIX_CONFIG_YAML")
            if yaml_path is None:
                return

        # 新しいパス解決ロジックを使用 (引数で受け取った depth を渡す)
        resolved_path = self._resolve_path(yaml_path=yaml_path, depth=depth)
        # resolved_path = os.path.abspath(yaml_path)

        print("resolved_path:", resolved_path)
        with open(resolved_path, "r") as f:
            data = yaml.safe_load(f)
        for k, v in data.items():
            setattr(self, k, v)

    @staticmethod
    def _resolve_path(
        *,
        yaml_path: Union[str, Path],
        depth: int,
    ) -> Path:
        """
        絶対パスならそのまま、相対パスならこのメソッドの呼び出し元を基準に解決する
        """
        path = Path(yaml_path)

        # 1. 絶対パス判定（/ や C:\\ など）
        if path.is_absolute():
            return path
            # return path  # / や C:\\ から始まれば、そのままのパスを返す

        # 2. 実行ファイルの場所を特定
        # クラスで呼び出す時
        #   stack[0]: _resolve_path
        #   stack[1]: load_yaml または _load_yaml
        #   stack[2]: Config.load(...) を書いたファイル
        # インスタンス変数(コンストラクタ)から呼び出す時
        #   stack[0] = _resolve_path
        #   stack[1] = load_yaml または _load_yaml
        #   stack[2] = __init__
        #   stack[3] = config = Config(...) を書いたファイル
        caller_frame = inspect.stack()[depth]
        caller_file = Path(caller_frame.filename).resolve()

        # 3. 実行ファイルのディレクトリ + 相対パス を結合
        return (caller_file.parent / path).resolve()
