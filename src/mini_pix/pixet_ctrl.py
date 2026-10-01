######################################################
import os
import site
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

# Python 3.7 では add_dll_directory は使えないため PATH を変更
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)
######################################################

import h5py
import numpy as np
import pypixet
import tifffile


class MiniPixCtrl:
    """
    MiniPIX / Timepix のローカル制御クラス。

    このクラスは gRPC、GUI、server/client 設定を一切扱わない。
    ローカルで単独利用できることを前提とする。

    測定:
        acquire()
            共通測定 API。
            acquisition_type="frames" / "integral" を指定する。

        acquire_frames()
            通常の複数フレーム測定用上位 API。

        acquire_integral()
            PIXet の doSimpleIntegralAcquisition() を使用する
            Integral 測定用上位 API。
            Python 側では画像を積算しない。

    フレーム:
        Frames 測定では、callback を指定した場合は
        PX_EVENT_ACQ_FINISHED ごとに最新フレームを取得する。

        callback の有無に関係なく、測定結果は内部メモリに保持する。

        get_current_frame()
            現在の最新フレームを返す。

        get_frame()
            内部履歴の指定フレームを返す。

        get_frames()
            内部履歴を全て返す。

    保存:
        TIFF
            1 frame = 1 TIFF。
            表示用変換を行わず、取得した数値配列を保存する。

        HDF5
            Frames 測定ではフレーム完成ごとに逐次追記して flush する。
            Integral 測定では最終積算フレームのみ保存する。

        PIXET_NATIVE
            PIXet 自身の保存機能を使用する。

    logger:
        logger は必須。
    """

    def __init__(
        self,
        logger: Any,
        log_level: Optional[str] = None,
    ):
        if logger is None:
            raise ValueError("logger is required")

        self._logger = logger
        self._log_level = log_level

        self._dev = None
        self._pixcfg = None
        self._pixet = None
        self._connected = False

        self._frames: List[Dict[str, Any]] = []
        self._current_frame: Optional[Dict[str, Any]] = None

        self._state_lock = threading.Lock()
        self._state = "disconnected"
        self._requested_count = 0
        self._finished_count = 0
        self._last_error = None

        self._event_callback = None

    # ------------------------------------------------------------
    # 接続
    # ------------------------------------------------------------

    def connect(self) -> bool:
        if self._connected:
            return True

        self._logger.info("pixet core init...")

        pypixet.start()
        self._pixet = pypixet.pixet

        devices = self._pixet.devices()

        if len(devices) == 0:
            self._logger.error("No devices found")
            pypixet.exit()
            self._pixet = None
            return False

        self._dev = devices[0]

        if self._dev.fullName() == "FileDevice 0":
            self._logger.error(
                "No physical detector found. Pixet returned FileDevice 0."
            )
            pypixet.exit()
            self._dev = None
            self._pixet = None
            return False

        self._logger.info("device:")
        self._logger.info("  fullName :" + str(self._dev.fullName()))
        self._logger.info("  deviceType:" + str(self._dev.deviceType()))
        self._logger.info("  chipType  :" + str(self._dev.chipType()))

        di = self._pixet.DevInfo()
        rc = self._dev.deviceInfo(di)

        self._logger.info("DevInfo:")
        self._logger.info("  rc     :" + str(rc))
        self._logger.info("  name   :" + str(di.name))
        self._logger.info("  serial :" + str(di.serial))
        self._logger.info("  type   :" + str(di.type))
        self._logger.info("  vendor :" + str(di.vendor))

        self._pixcfg = self._dev.pixCfg()
        self._connected = True

        with self._state_lock:
            self._state = "idle"
            self._last_error = None

        return True

    def disconnect(self):
        if not self._connected:
            return

        self._logger.info("pixet core exit...")

        try:
            if self.is_running():
                self.stop()
        except Exception:
            pass

        if self._pixet is not None:
            try:
                self._pixet.exitPixet()
            except Exception:
                pass

        try:
            pypixet.exit()
        finally:
            self._dev = None
            self._pixcfg = None
            self._pixet = None
            self._connected = False

            with self._state_lock:
                self._state = "disconnected"

    def _require_connected(self):
        if not self._connected:
            raise RuntimeError("MiniPIX is not connected")

    # ------------------------------------------------------------
    # 検出器設定
    # ------------------------------------------------------------

    def set_mode_all(
        self,
        mode: str,
    ) -> bool:
        self._require_connected()

        mode_map = {
            "Counting": self._pixet.PX_TPXMODE_MEDIPIX,
            "Energy": self._pixet.PX_TPXMODE_TOT,
            "Time": self._pixet.PX_TPXMODE_TIMEPIX,
        }

        if mode not in mode_map:
            self._logger.error(
                "Invalid mode: " + str(mode) + '. Use "Counting", "Energy", or "Time".'
            )
            return False

        rc = self._pixcfg.setModeAll(mode_map[mode])

        if rc != 0:
            self._logger.error(
                "setModeAll failed: rc="
                + str(rc)
                + ", err="
                + str(self._dev.lastError())
            )
            return False

        rc = self._pixcfg.setToDevice()

        if rc != 0:
            self._logger.error(
                "setToDevice failed: rc="
                + str(rc)
                + ", err="
                + str(self._dev.lastError())
            )
            return False

        return True

    def set_threshold(
        self,
        threshold_kev: float,
    ) -> bool:
        self._require_connected()

        rc = self._dev.setThreshold(
            0,
            threshold_kev,
            self._pixet.PX_THLFLG_ENERGY,
        )

        if rc != 0:
            self._logger.error(
                "setThreshold failed: rc="
                + str(rc)
                + ", err="
                + str(self._dev.lastError())
            )
            return False

        return True

    def set_clock(
        self,
        clock_mhz: float,
    ) -> bool:
        self._require_connected()

        rc = self._dev.setTimepixClock(clock_mhz)

        if rc != 0:
            self._logger.error(
                "setTimepixClock failed: rc="
                + str(rc)
                + ", err="
                + str(self._dev.lastError())
            )
            return False

        return True

    def set_bias(
        self,
        bias_volt: float,
    ) -> bool:
        self._require_connected()

        rc = self._dev.setBias(bias_volt)

        if rc != 0:
            self._logger.error(
                "setBias failed: rc=" + str(rc) + ", err=" + str(self._dev.lastError())
            )
            return False

        return True

    # ------------------------------------------------------------
    # フレーム変換
    # ------------------------------------------------------------

    def get_frame_size(
        self,
        frame,
        data_len: int,
    ) -> Tuple[int, int]:
        self._require_connected()

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
            raise RuntimeError(
                "cannot infer frame size from pixel count: " + str(data_len)
            )

        return side, side

    def _frame_to_dict(
        self,
        frame,
    ) -> Dict[str, Any]:
        frame_name = "frame"

        try:
            frame_name = str(frame.frameName())
        except Exception:
            pass

        raw_data = np.asarray(frame.data()).copy()

        width, height = self.get_frame_size(
            frame,
            int(raw_data.size),
        )

        data = raw_data.reshape(
            height,
            width,
        )

        item = {
            "name": frame_name,
            "width": width,
            "height": height,
            "data": data,
            "minimum": data.min().item(),
            "maximum": data.max().item(),
            "nonzero": int(np.count_nonzero(data)),
            "subframes": [],
        }

        try:
            subframes = list(frame.subFrames())
        except Exception:
            subframes = []

        for sub in subframes:
            try:
                sub_name = "subframe"

                try:
                    sub_name = str(sub.frameName())
                except Exception:
                    pass

                sub_raw_data = np.asarray(sub.data()).copy()

                sub_width, sub_height = self.get_frame_size(
                    sub,
                    int(sub_raw_data.size),
                )

                sub_data = sub_raw_data.reshape(
                    sub_height,
                    sub_width,
                )

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

    def _read_frame_at(
        self,
        index: int,
    ) -> Dict[str, Any]:
        frame = self._dev.acqFrameRefInc(index)

        try:
            return self._frame_to_dict(frame)
        finally:
            try:
                frame.destroy()
            except Exception:
                pass

    def _read_last_frame(
        self,
    ) -> Dict[str, Any]:
        frame = self._dev.lastAcqFrameRefInc()

        try:
            return self._frame_to_dict(frame)
        finally:
            try:
                frame.destroy()
            except Exception:
                pass

    def _store_frame(
        self,
        frame: Dict[str, Any],
    ):
        self._frames.append(frame)
        self._current_frame = frame

        with self._state_lock:
            self._finished_count = len(self._frames)

    # ------------------------------------------------------------
    # メモリ上の測定結果
    # ------------------------------------------------------------

    def clear_frames(self):
        self._frames = []
        self._current_frame = None

    def get_frame_count(self) -> int:
        return len(self._frames)

    def get_frame(
        self,
        index: int,
    ) -> Dict[str, Any]:
        return self._frames[index]

    def get_frames(
        self,
    ) -> List[Dict[str, Any]]:
        return list(self._frames)

    def get_current_frame(
        self,
    ) -> Optional[Dict[str, Any]]:
        return self._current_frame

    # 既存 PIXet メモリを直接確認したい場合の低レベル API
    def get_acq_frame_count(self) -> int:
        self._require_connected()

        return int(self._dev.acqFrameCount())

    def get_acq_frames(
        self,
        idx: Optional[int] = None,
    ) -> Dict[str, Any]:
        self._require_connected()

        frames = []

        if idx is None:
            frame_count = self.get_acq_frame_count()

            for frame_index in range(frame_count):
                frames.append(self._read_frame_at(frame_index))
        else:
            frame_count = 1
            frames.append(self._read_frame_at(idx))

        return {
            "frame_count": frame_count,
            "frames": frames,
        }

    # ------------------------------------------------------------
    # 保存
    # ------------------------------------------------------------

    def _normalize_save_format(
        self,
        save_format: Optional[str],
    ) -> str:
        if save_format is None:
            return "NONE"

        value = str(save_format).strip().upper()

        if value == "":
            return "NONE"

        if value == "PIXET NATIVE":
            return "PIXET_NATIVE"

        return value

    def _prepare_save(
        self,
        save_format: Optional[str],
        save_path: Optional[str],
    ) -> Tuple[str, str]:
        normalized = self._normalize_save_format(save_format)

        supported = {
            "NONE",
            "TIFF",
            "HDF5",
            "PIXET_NATIVE",
        }

        if normalized not in supported:
            raise ValueError("Unsupported save_format: " + str(save_format))

        path = ""

        if save_path is not None:
            path = str(save_path)

        if normalized != "NONE":
            if path == "":
                raise ValueError("save_path is required when saving is enabled")

        return normalized, path

    def _save_tiff_frame(
        self,
        directory: str,
        frame_index: int,
        frame: Dict[str, Any],
    ):
        os.makedirs(
            directory,
            exist_ok=True,
        )

        filename = os.path.join(
            directory,
            "frame_" + str(frame_index + 1).zfill(6) + ".tiff",
        )

        tifffile.imwrite(
            filename,
            frame["data"],
        )

    def _open_hdf5(
        self,
        filename: str,
    ):
        parent = os.path.dirname(os.path.abspath(filename))

        if parent != "":
            os.makedirs(
                parent,
                exist_ok=True,
            )

        h5_file = h5py.File(
            filename,
            "w",
        )

        return h5_file

    def _append_hdf5_frame(
        self,
        h5_file,
        frame: Dict[str, Any],
    ):
        data = frame["data"]

        if "frames" not in h5_file:
            h5_file.create_dataset(
                "frames",
                shape=(
                    0,
                    int(data.shape[0]),
                    int(data.shape[1]),
                ),
                maxshape=(
                    None,
                    int(data.shape[0]),
                    int(data.shape[1]),
                ),
                chunks=(
                    1,
                    int(data.shape[0]),
                    int(data.shape[1]),
                ),
                dtype=data.dtype,
            )

        dataset = h5_file["frames"]

        frame_index = int(dataset.shape[0])

        dataset.resize(
            frame_index + 1,
            axis=0,
        )

        dataset[
            frame_index,
            :,
            :,
        ] = data

        h5_file.flush()

    # ------------------------------------------------------------
    # 測定
    # ------------------------------------------------------------

    def acquire(
        self,
        count: int,
        sec: float,
        acquisition_type: str = "frames",
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        save_format: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        共通測定 API。

        Args:
            count:
                測定回数。

            sec:
                1回あたりの測定時間 [s]。

            acquisition_type:
                "frames" または "integral"。

            callback:
                Frames 測定では、各フレーム完成時に呼ばれる。
                Integral 測定では途中フレームには使用せず、
                最終積算フレーム完成後に1回だけ呼ばれる。

            save_format:
                None / "TIFF" / "HDF5" / "PIXET_NATIVE"

            save_path:
                TIFF:
                    保存先ディレクトリ。
                HDF5:
                    HDF5 ファイル名。
                PIXET_NATIVE:
                    PIXet native ファイル名。

        Returns:
            dict:
                rc
                acquisition_type
                frame_count
                frames
                saved_file

        Notes:
            Integral は PIXet の doSimpleIntegralAcquisition() を使用する。
            Python 側で画像を積算しない。
        """
        self._require_connected()

        acquisition = str(acquisition_type).strip().lower()

        if acquisition not in {
            "frames",
            "integral",
        }:
            raise ValueError("acquisition_type must be " '"frames" or "integral"')

        normalized_save_format, normalized_save_path = self._prepare_save(
            save_format,
            save_path,
        )

        self.clear_frames()

        with self._state_lock:
            self._state = "running"
            self._requested_count = int(count)
            self._finished_count = 0
            self._last_error = None

        h5_file = None
        self._event_callback = None

        pixet_file_type = self._pixet.PX_FTYPE_NONE
        pixet_file_name = ""

        if normalized_save_format == "PIXET_NATIVE":
            pixet_file_type = self._pixet.PX_FTYPE_AUTODETECT
            pixet_file_name = normalized_save_path

        if normalized_save_format == "HDF5":
            h5_file = self._open_hdf5(normalized_save_path)

        try:
            if acquisition == "frames":
                need_event = False

                if callback is not None:
                    need_event = True

                if normalized_save_format == "TIFF":
                    need_event = True

                if normalized_save_format == "HDF5":
                    need_event = True

                if need_event:

                    def acquisition_finished(_finished_count):
                        frame = self._read_last_frame()

                        self._store_frame(frame)

                        frame_index = len(self._frames) - 1

                        if normalized_save_format == "TIFF":
                            self._save_tiff_frame(
                                normalized_save_path,
                                frame_index,
                                frame,
                            )

                        if normalized_save_format == "HDF5":
                            self._append_hdf5_frame(
                                h5_file,
                                frame,
                            )

                        if callback is not None:
                            callback(frame)

                    self._event_callback = acquisition_finished

                    self._dev.registerEvent(
                        self._pixet.PX_EVENT_ACQ_FINISHED,
                        0,
                        self._event_callback,
                    )

                self._logger.info(
                    "doSimpleAcquisition start: count="
                    + str(count)
                    + ", sec="
                    + str(sec)
                )

                rc = self._dev.doSimpleAcquisition(
                    count,
                    sec,
                    pixet_file_type,
                    pixet_file_name,
                )

                self._logger.info("doSimpleAcquisition end: rc=" + str(rc))

                if not need_event:
                    frame_count = int(self._dev.acqFrameCount())

                    for frame_index in range(frame_count):
                        frame = self._read_frame_at(frame_index)

                        self._store_frame(frame)

                if rc != 0:
                    with self._state_lock:
                        current_state = self._state

                    if current_state != "aborting":
                        raise RuntimeError(
                            "doSimpleAcquisition failed: rc="
                            + str(rc)
                            + ", err="
                            + str(self._dev.lastError())
                        )

            else:
                self._logger.info(
                    "doSimpleIntegralAcquisition start: count="
                    + str(count)
                    + ", sec="
                    + str(sec)
                )

                rc = self._dev.doSimpleIntegralAcquisition(
                    count,
                    sec,
                    pixet_file_type,
                    pixet_file_name,
                )

                self._logger.info("doSimpleIntegralAcquisition end: rc=" + str(rc))

                if rc == 0:
                    frame_count = int(self._dev.acqFrameCount())

                    if frame_count > 0:
                        frame = self._read_last_frame()

                        self._store_frame(frame)

                        if normalized_save_format == "TIFF":
                            self._save_tiff_frame(
                                normalized_save_path,
                                0,
                                frame,
                            )

                        if normalized_save_format == "HDF5":
                            self._append_hdf5_frame(
                                h5_file,
                                frame,
                            )

                        if callback is not None:
                            callback(frame)

                    with self._state_lock:
                        self._finished_count = int(count)

                else:
                    with self._state_lock:
                        current_state = self._state

                    if current_state != "aborting":
                        raise RuntimeError(
                            "doSimpleIntegralAcquisition failed: rc="
                            + str(rc)
                            + ", err="
                            + str(self._dev.lastError())
                        )

            with self._state_lock:
                if self._state == "running":
                    self._state = "finished"

                if self._state == "aborting":
                    self._state = "stopped"

            result = {
                "rc": int(rc),
                "acquisition_type": acquisition,
                "frame_count": len(self._frames),
                "frames": self.get_frames(),
                "saved_file": pixet_file_name,
            }

            if normalized_save_format == "TIFF":
                result["saved_file"] = normalized_save_path

            if normalized_save_format == "HDF5":
                result["saved_file"] = normalized_save_path

            return result

        except Exception as error:
            with self._state_lock:
                self._state = "error"
                self._last_error = str(error)

            raise

        finally:
            if self._event_callback is not None:
                try:
                    self._dev.unregisterEvent(
                        self._pixet.PX_EVENT_ACQ_FINISHED,
                        0,
                        self._event_callback,
                    )
                finally:
                    self._event_callback = None

            if h5_file is not None:
                h5_file.flush()
                h5_file.close()

    def acquire_frames(
        self,
        count: int,
        sec: float,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        save_format: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        通常の frame 測定用上位 API。
        """
        return self.acquire(
            count=count,
            sec=sec,
            acquisition_type="frames",
            callback=callback,
            save_format=save_format,
            save_path=save_path,
        )

    def acquire_integral(
        self,
        count: int,
        sec: float,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        save_format: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Integral 測定用上位 API。

        PIXet の doSimpleIntegralAcquisition() を使用する。
        Python 側では画像を積算しない。

        callback を指定した場合も、積算途中では呼ばず、
        最終積算フレーム完成後に1回だけ呼ぶ。
        """
        return self.acquire(
            count=count,
            sec=sec,
            acquisition_type="integral",
            callback=callback,
            save_format=save_format,
            save_path=save_path,
        )

    # ------------------------------------------------------------
    # 測定停止・状態
    # ------------------------------------------------------------

    def stop(self):
        self._require_connected()

        if not self._dev.isAcquisitionRunning():
            return

        with self._state_lock:
            self._state = "aborting"

        self._dev.abortOperation()

    def is_running(self) -> bool:
        if not self._connected:
            return False

        return bool(self._dev.isAcquisitionRunning())

    def is_aborting(self) -> bool:
        if not self._connected:
            return False

        return bool(self._dev.isAcquisitionAborting())

    def state(self) -> Dict[str, Any]:
        if not self._connected:
            with self._state_lock:
                state = self._state
                requested_count = self._requested_count
                finished_count = self._finished_count
                last_error = self._last_error

            return {
                "state": state,
                "running": False,
                "aborting": False,
                "requested_count": requested_count,
                "finished_count": finished_count,
                "frame_count": len(self._frames),
                "last_error": last_error,
            }

        running = bool(self._dev.isAcquisitionRunning())
        aborting = bool(self._dev.isAcquisitionAborting())

        with self._state_lock:
            state = self._state
            requested_count = self._requested_count
            finished_count = self._finished_count
            last_error = self._last_error

        return {
            "state": state,
            "running": running,
            "aborting": aborting,
            "requested_count": requested_count,
            "finished_count": finished_count,
            "frame_count": len(self._frames),
            "last_error": last_error,
        }
