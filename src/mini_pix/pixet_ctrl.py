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
    """
    今基本的には MPX2 相当で作っている
    """

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

        # --- 基本オブジェクト
        self._dev = None
        self._pixcfg = None
        self._pixet = None

    def disconnect(self):
        self._logger.info("pixet core exit...")

        if self._pixet is not None:
            try:
                self._pixet.exitPixet()
            except Exception:
                pass

        pypixet.exit()

        self._dev = None
        self._pixcfg = None
        self._pixet = None

    def connect(self) -> bool:
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
            self._logger.error("No devices found")
            return False

        self._dev = devices[0]

        if self._dev.fullName() == "FileDevice 0":
            self._logger.error(
                "No physical detector found. Pixet returned FileDevice 0."
            )
            return False

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

        # デフォルト設定: GUI の「Counting」と同じモード
        rc = self._pixcfg.setModeAll(
            # DAC 一覧
            # 全pixelを ToT モードに設定
            # 0 COUNT 一定時間内にヒットした回数（カウント数）を記録
            # 1 TOT (Time Over Threshold) しきい値を超えていた時間幅を記録 → エネルギーに比例
            # 2 TOA (Time Of Arrival) しきい値を超えた時刻を記録
            # 3 ONEHIT 最初の1ヒットのみ記録
            self._pixet.PX_TPXMODE_TOT,
        )
        if rc != 0:
            self._logger.error(
                f"setModeAll failed: rc={rc}, err={self._dev.lastError()}"
            )
            return False

        rc = self._pixcfg.setToDevice()
        if rc != 0:
            self._logger.error(
                f"setToDevice failed: rc={rc}, err={self._dev.lastError()}"
            )
            return False

        return True

    # MPX2 では使えない
    # def set_auto_range(self, enable: bool):
    #     self._pixcfg.setAutoRange(auto_range)

    # MPX2 では使えない
    # def set_range(self, min_val: int, max_val: int):
    #     self._pixcfg.setRange(min_val, max_val)

    def set_mode_all(
        self,
        mode: str,
    ) -> bool:
        """
        GUI の Detector Settings -> Mode と同じ名称で全 pixel のモードを設定する。

        Args:
            mode (str): "Counting", "Energy", "Time" のいずれか。

        Returns:
            bool: 設定に成功した場合 True。
        """
        mode_map = {
            "Counting": self._pixet.PX_TPXMODE_MEDIPIX,
            "Energy": self._pixet.PX_TPXMODE_TOT,
            "Time": self._pixet.PX_TPXMODE_TIMEPIX,
        }

        if mode not in mode_map:
            self._logger.error(
                f"Invalid mode: {mode}. "
                'Use "Counting", "Energy", or "Time".'
            )
            return False

        pixet_const = mode_map[mode]

        rc = self._pixcfg.setModeAll(pixet_const)
        if rc != 0:
            self._logger.error(
                f"setModeAll failed: rc={rc}, err={self._dev.lastError()}"
            )
            return False

        rc = self._pixcfg.setToDevice()
        if rc != 0:
            self._logger.error(
                f"setToDevice failed: rc={rc}, err={self._dev.lastError()}"
            )
        return True

    def set_threshold(
        self,
        threshold_kev: float,
    ) -> bool:
        """
        keV

        Args:
            threshold_kev:

        Returns:

        """
        # デバイス全体の設定と測定実行
        rc = self._dev.setThreshold(
            0,  # chip chip index（通常 0）
            threshold_kev,  # value threshold
            self._pixet.PX_THLFLG_ENERGY,  # keV 単位指定(GUIと同じ)
        )
        # PX_THLFLAG_DAC: DAC値
        # PX_THLFLG_ENERGY: keV
        if rc != 0:
            self._logger.error(
                f"setThreshold failed: rc={rc}, err={self._dev.lastError()}"
            )
            return False
        return True

    def set_clock(
        self,
        clock_mhz: float,
    ) -> bool:
        """
        MHz

        Args:
            clock_mhz:

        Returns:

        """
        rc = self._dev.setTimepixClock(clock_mhz)
        if rc != 0:
            self._logger.error(
                f"setTimepixClock failed: rc={rc}, err={self._dev.lastError()}"
            )
            return False
        return True

    def set_bias(
        self,
        bias_volt: float,
    ) -> bool:
        """
        V

        Args:
            bias_volt (float):  V

        Returns:

        """
        rc = self._dev.setBias(bias_volt)
        if rc != 0:
            self._logger.error(f"setBias failed: rc={rc}, err={self._dev.lastError()}")
            return False
        return True

    # ----------------------------
    # 撮像をメモリに入れるためのサポート
    # ----------------------------

    def _frame_to_dict(self, frame) -> dict:
        frame_name = "frame"
        try:
            frame_name = str(frame.frameName())
        except Exception:
            pass

        data = list(frame.data())
        width, height = self.get_frame_size(frame, len(data))

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
                sub_width, sub_height = self.get_frame_size(sub, len(sub_data))
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

    # ----------------------------
    # 撮像
    # ----------------------------

    def get_frame_size(
        self,
        frame,
        data_len: int,
    ) -> Tuple[int, int]:
        """

        Args:
            frame:
            data_len:

        Returns:

        """
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

    def get_acq_frame_count(self) -> int:
        # acqFrameCount()
        frame_count = int(self._dev.acqFrameCount())
        return frame_count

    def get_acq_frames(
        self,
        idx: Optional[int] = None,
    ) -> dict:
        """

        Args:
            idx:

        Returns:

        """
        frames = []
        if idx is None:
            # 現在メモリにあるフレーム数
            frame_count = self.get_acq_frame_count()

            for idx in range(frame_count):
                frame = self._dev.acqFrameRefInc(idx)
                try:
                    frames.append(self._frame_to_dict(frame))
                finally:
                    try:
                        frame.destroy()
                    except Exception:
                        pass

        else:
            # 指定の1フレーム
            frame_count = 1
            frame = self._dev.acqFrameRefInc(idx)
            frames.append(self._frame_to_dict(frame))
            try:
                frame.destroy()
            except Exception:
                pass

        return {
            "frame_count": frame_count,
            "frames": frames,
        }

    def get_acq_data_count(self):
        # acqDataCount()
        pass

    def get_acq_data(self, idx) -> dict:
        # acqDataRefInc()
        pass

    def simple_int_acq(
        self,
        count: int,
        sec: float,
        name: str = "example.png",
        file_type: str = "NONE",
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
        name: str = "example.png",
        file_type: str = "AUTODETECT",
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
        self._logger.info(f"== simple_acq()")

        file_type_const = {
            "PNG": self._pixet.PX_FTYPE_PNG,
            "TPX3_PIXELS": self._pixet.PX_FTYPE_TPX3_PIXELS,
            "BINARY_FRAME": self._pixet.PX_FTYPE_BINARY_FRAME,
            "NONE": self._pixet.PX_FTYPE_NONE,
            "AUTODETECT": self._pixet.PX_FTYPE_AUTODETECT,
        }[file_type]

        if save_file:
            if file_type == "NONE":
                output_name = ""
            else:
                output_name = name
        else:
            output_name = ""

        self._logger.info(f"file_type = {file_type}")
        self._logger.info(f"output_name = {output_name}")
        self._logger.info(f"count = {count}")
        self._logger.info(f"sec = {sec}")
        self._logger.info(f"")

        self._logger.info(
            f"dev.doSimpleAcquisition ({count} frames @ {sec} sec) - start"
        )
        rc = self._dev.doSimpleAcquisition(
            count,  # count (Acqの回数=フレーム数)
            sec,  # 測定時間
            file_type_const,  # self._pixet.PX_FTYPE_AUTODETECT,  # 保存形式
            output_name,  # ファイル名
        )
        self._logger.info(f"dev.doSimpleAcquisition - end: {rc} (0 is OK)")

        if rc != 0:
            self._logger.error(f"doSimpleAcquisition failed: rc={rc}")
            return False

        result = {
            "rc": int(rc),
            "saved_file": output_name,
        }
        result.update(self.get_acq_frames())
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
    ctrl = MiniPixCtrl(logger=logger_)

    ctrl.connect()
    ctrl.set_mode_all("Counting")
    # ctrl.set_threshold(1000)
    ctrl.set_threshold(6.0)
    ctrl.set_bias(150)  # V
    ctrl.set_clock(9.66667)  # Mhz
    ctrl.simple_acq(1, 3, "example.png")
    ctrl.disconnect()
