######################################################
import os
import site

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

# Python 3.7 では add_dll_directory は使えないため PATH を変更
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)  # .pyd を import 可能にする
######################################################
from typing import Any, Optional, Set, Dict, List, Union, Tuple, Type, TypeVar

from x_logger import XLogger
import pypixet


class MiniPixCtrl:
    def __init__(
        self,
        logger: Optional[Any] = None,
        log_level: Optional[str] = None,
    ):
        # XLogger が存在しない時に仕方がないのでデフォルトの logging を使う
        if logger is None:
            import logging

            log_level = log_level or "INFO"
            logging.basicConfig(level=log_level.upper())
            logger = logging.getLogger(__name__)
            # logger = get_silent_logger())

        self._logger = logger
        self._dev = None
        self._pixcfg = None
        self._pixet = None

    def disconnect(self):
        self._logger.info("pixet core exit...")
        pypixet.exit()

    def connect(self):
        self._logger.info("pixet core init...")
        # Piext core の起動
        pypixet.start()

        # Pixet core のハンドル（メインオブジェクト）を取得
        self._pixet = pypixet.pixet

        # もし、 pixet.devices() だと全デバイス
        # TPX3 デバイスのみ取得。
        # pixet.deviceByName(name)
        #   --> GUI で表示されるデバイス名の指定
        # devices = pixet.devicesByType(pixet.PX_DEVTYPE_TPX3)
        devices = self._pixet.devices()

        if len(devices) == 0:
            raise RuntimeError("No devices found")

        self._dev = devices[0]

        self._logger.info("device:")
        self._logger.info(f"  fullName :{self._dev.fullName()}")
        self._logger.info(f"  deviceType:{self._dev.deviceType()}")
        self._logger.info(f"  chipType  :{self._dev.chipType()}")

        # --- DevInfo ---
        di = self._pixet.DevInfo()
        rc = self._dev.deviceInfo(di)

        self._logger.info("DevInfo:")
        self._logger.info(f"  rc     :{rc}")
        self._logger.info(f"  name   :{di.name}")
        self._logger.info(f"  serial :{di.serial}")
        self._logger.info(f"  type   :{di.type}")
        self._logger.info(f"  vendor :{di.vendor}")

        # ==========================================================
        # Timepix (Mpx2) は setOperationMode を使わない
        # → pixel configuration で mode を設定
        # dev.setOperationMode(pixet.PX_TPX3_OPM_EVENT_ITOT)
        # ==========================================================

        # 各ピクセルに展開される行列設定
        # mode, mask, pixel ごとの threshoild correction
        self._pixcfg = self._dev.pixCfg()

        # 全ビクセル
        self._pixcfg.setModeAll(
            # DAC 一覧
            # 全pixelを ToT モードに設定
            # 0 COUNT 一定時間内にヒットした回数（カウント数）を記録
            # 1 TOT (Time Over Threshold) しきい値を超えていた時間幅を記録 → エネルギーに比例
            # 2 TOA (Time Of Arrival) しきい値を超えた時刻を記録
            # 3 ONEHIT 最初の1ヒットのみ記録
            self._pixet.PX_TPXMODE_TOT,
        )

    def set_mode_all(
        self,
        mode: str,
    ):
        const_name = {
            "COUNT": "PX_TPXMODE_MEDIPIX",
            "TOT": "PX_TPXMODE_TOT",
            "TOA": "PX_TPXMODE_TIMEPIX",
            "ONEHIT": "PX_TPXMODE_1HIT",
        }[mode]

        pixet_const = getattr(
            self._pixet,
            const_name,
        )

        self._pixcfg.setModeAll(
            pixet_const,
        )
        self._pixcfg.setToDevice()

    def set_threshold(
        self,
        threshold: float,
    ):
        # デバイス全体の設定と測定実行
        self._dev.setThreshold(
            0,  # chip chip index（通常 0）
            threshold,  # value threshold
            self._pixet.PX_THLFLG_ENERGY,  # flag 単位指定
        )

    # ----------------------------
    # 撮像をメモリに入れるためのサポート
    # ----------------------------

    def _get_frame_size(
        self,
        frame,
        data_len: int,
    ) -> Tuple[int, int]:
        for obj in (frame, self._dev):
            try:
                width = int(obj.width())
                height = int(obj.height())
                if width > 0 and height > 0:
                    return width, height
            except Exception:
                pass

        side = int(data_len**0.5)
        if side * side != data_len:
            raise RuntimeError(f"cannot infer frame size from pixel count: {data_len}")
        return side, side

    def _frame_to_dict(self, frame) -> dict:
        frame_name = "frame"
        try:
            frame_name = str(frame.frameName())
        except Exception:
            pass

        data = list(frame.data())
        width, height = self._get_frame_size(frame, len(data))

        item = {
            "name": frame_name,
            "width": width,
            "height": height,
            "data": data,
            "subframes": [],
        }

        try:
            subframes = list(frame.subFrames())
        except Exception:
            subframes = []

        for sub in subframes:
            try:
                sub_name = str(sub.frameName())
            except Exception:
                sub_name = "subframe"

            try:
                sub_data = list(sub.data())
                sub_width, sub_height = self._get_frame_size(sub, len(sub_data))
                item["subframes"].append(
                    {
                        "name": sub_name,
                        "width": sub_width,
                        "height": sub_height,
                        "data": sub_data,
                    }
                )
            finally:
                try:
                    sub.destroy()
                except Exception:
                    pass

        return item

    def _collect_acq_frames(self) -> dict:
        frame_count = int(self._dev.acqFrameCount())
        frames = []

        for idx in range(frame_count):
            frame = self._dev.acqFrameRefInc(idx)
            try:
                frames.append(self._frame_to_dict(frame))
            finally:
                try:
                    frame.destroy()
                except Exception:
                    pass

        return {
            "frame_count": frame_count,
            "frames": frames,
        }

    # ----------------------------
    # 撮像
    # ----------------------------

    def simple_int_acq(
        self,
        count: int,
        sec: float,
        file_type=self._pixet.PX_FTYPE_AUTODETECT,
        name: str = "example.png",
        *,
        save_file: bool = True,
        return_data: bool = False,
    ):
        """
        積算 SimpleAcq モード
        """
        pass

    def simple_acq(
        self,
        count: int,
        sec: float,
        file_type=self._pixet.PX_FTYPE_AUTODETECT,
        name: str = "example.png",
        *,
        save_file: bool = True,
        return_data: bool = False,
    ):
        """
        通常の frame モードで、指定した数のフレームを取得する。
        取得された各フレームは個別に扱われる。

        Args:
            count:
            sec:
            name:
            file_type: 保存形式
            save_file:
            return_data:

        Returns:

        """
        self._logger.info("dev.doSimpleAcquisition (3 frames @ 1 sec) - start")

        output_name = name if save_file else ""

        rc = self._dev.doSimpleAcquisition(
            count,  # count (Acqの回数=フレーム数)
            sec,  # 測定時間
            file_type,  # self._pixet.PX_FTYPE_AUTODETECT,  # 保存形式
            output_name,  # ファイル名
        )
        self._logger.info(f"dev.doSimpleAcquisition - end: {rc} (0 is OK)")

        if rc != 0:
            raise RuntimeError(f"doSimpleAcquisition failed: rc={rc}")

        if not return_data:
            return rc

        result = {
            "rc": int(rc),
            "saved_file": output_name,
        }
        result.update(self._collect_acq_frames())
        return result

        # self._pixet.PX_FTYPE_PNG
        # self._pixet.PX_FTYPE_TPX3_PIXELS
        # self._pixet.PX_FTYPE_BINARY_FRAME
        # self._pixet.PX_FTYPE_NONE

        # using only for old pxcore versions up-to 1.8.3
        # - save settings, correct stop devices and core exit
        # - use both lines
        # pixet.exitPixet()

        # some USB devices must be power cycled
        # if it not used / important if third-party debug environment used


if __name__ == "__main__":
    logger_ = XLogger(log_level="INFO")
    ctrl = MiniPixCtrl()

    ctrl.connect()
    ctrl.set_mode_all("TOT")
    ctrl.set_threshold(1000)
    ctrl.simple_acq(1, 1, "example.png")
    ctrl.disconnect()
