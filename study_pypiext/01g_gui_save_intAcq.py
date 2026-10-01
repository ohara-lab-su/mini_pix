import os
import site
import sys
import threading

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)

import numpy as np
import h5py
import tifffile
import pypixet

from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QSlider,
    QSizePolicy,
    QGraphicsView,
    QGraphicsScene,
    QFileDialog,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)


# ------------------------------------------------------------
# 測定条件
# ------------------------------------------------------------

TIME = 1
COUNT = 1

THRESHOLD = 2.4
BIAS = 150.0
CLOCK = 9.66667


# ------------------------------------------------------------
# PIXet / MiniPIX
# ------------------------------------------------------------

class MiniPIX:
    """
    PIXet / MiniPIX の初期化、設定、測定、停止、状態取得を担当する。

    GUI には依存しない。

    Frames:
        PIXet の doSimpleAcquisition() を使用する。
        Python 側で画像の積算は行わない。

    Integral:
        PIXet の doSimpleIntegralAcquisition() を使用する。
        PIXet 側で積算された最終フレームだけを取得する。

    callback:
        Frames 測定時のみ、各フレーム完了時に callback(frame_result) を呼ぶ。
        Integral 測定では途中フレームを callback しない。

    save:
        TIFF:
            1フレームを1ファイルとして保存する。
        HDF5:
            Frames 測定ではフレーム完了ごとに逐次追記する。
            Integral 測定では最終積算フレームのみ保存する。
        PIXet native:
            PIXet API 自身のファイル保存機能を使用する。
    """

    def __init__(self):
        self.pixet = None
        self.dev = None
        self._started = False
        self._event_callback = None

        self._state_lock = threading.Lock()
        self._state = "idle"
        self._requested_count = 0
        self._finished_count = 0
        self._last_error = None

        try:
            pypixet.start()
            self._started = True

            self.pixet = pypixet.pixet
            devices = self.pixet.devices()

            if len(devices) == 0:
                raise RuntimeError("No devices found")

            self.dev = devices[0]

            print(
                "Device:",
                self.dev.fullName(),
            )

        except Exception:
            self.close()
            raise

    def configure(
        self,
        mode,
        threshold,
        bias,
        clock,
    ):
        pixcfg = self.dev.pixCfg()

        if mode == "Counting":
            pixcfg.setModeAll(
                self.pixet.PX_TPXMODE_MEDIPIX
            )
        else:
            pixcfg.setModeAll(
                self.pixet.PX_TPXMODE_TOT
            )

        self.dev.setThreshold(
            0,
            threshold,
            self.pixet.PX_THLFLG_ENERGY,
        )

        self.dev.setBias(
            bias
        )

        self.dev.setTimepixClock(
            clock
        )

    def _read_frame(self, frame):
        try:
            data = np.array(
                frame.data()
            )

            data = data.reshape(
                256,
                256,
            )

            result = {
                "data": data.copy(),
                "minimum": data.min(),
                "maximum": data.max(),
                "nonzero": np.count_nonzero(data),
            }

        finally:
            frame.destroy()

        return result

    def _read_frame_at(self, index):
        frame = self.dev.acqFrameRefInc(
            index
        )

        return self._read_frame(
            frame
        )

    def _read_last_frame(self):
        frame = self.dev.lastAcqFrameRefInc()

        return self._read_frame(
            frame
        )

    def _save_tiff_frame(
        self,
        directory,
        frame_index,
        result,
    ):
        os.makedirs(
            directory,
            exist_ok=True,
        )

        filename = os.path.join(
            directory,
            "frame_"
            + str(frame_index + 1).zfill(6)
            + ".tiff",
        )

        tifffile.imwrite(
            filename,
            result["data"],
        )

    def _open_hdf5(
        self,
        filename,
    ):
        h5_file = h5py.File(
            filename,
            "w",
        )

        dataset = h5_file.create_dataset(
            "frames",
            shape=(0, 256, 256),
            maxshape=(None, 256, 256),
            chunks=(1, 256, 256),
            dtype=np.uint32,
        )

        return h5_file, dataset

    def _append_hdf5_frame(
        self,
        h5_file,
        dataset,
        result,
    ):
        frame_index = dataset.shape[0]

        dataset.resize(
            frame_index + 1,
            axis=0,
        )

        dataset[
            frame_index,
            :,
            :,
        ] = result["data"]

        h5_file.flush()

    def acquire(
        self,
        count,
        measurement_time,
        acquisition_type="Frames",
        callback=None,
        save_format="None",
        save_path="",
    ):
        """
        MiniPIX の共通測定API。

        acquisition_type:
            "Frames"
            "Integral"

        save_format:
            "None"
            "TIFF"
            "HDF5"
            "PIXet native"

        Frames + HDF5/TIFF:
            PX_EVENT_ACQ_FINISHED ごとに保存する。
            GUI callback の有無とは独立している。

        Integral:
            doSimpleIntegralAcquisition() を使用する。
            Python側で積算しない。
            最終積算フレームだけを取得・保存・返却する。
        """
        frames = []
        h5_file = None
        h5_dataset = None

        pixet_file_type = self.pixet.PX_FTYPE_NONE
        pixet_file_name = ""

        if save_format == "PIXet native":
            pixet_file_type = self.pixet.PX_FTYPE_AUTODETECT
            pixet_file_name = save_path

        if save_format == "HDF5":
            h5_file, h5_dataset = self._open_hdf5(
                save_path
            )

        with self._state_lock:
            self._state = "running"
            self._requested_count = count
            self._finished_count = 0
            self._last_error = None

        try:
            if acquisition_type == "Frames":
                need_frame_event = False

                if callback is not None:
                    need_frame_event = True

                if save_format == "TIFF":
                    need_frame_event = True

                if save_format == "HDF5":
                    need_frame_event = True

                if need_frame_event:
                    def acquisition_finished(finished_count):
                        result = self._read_last_frame()

                        frames.append(
                            result
                        )

                        frame_index = len(frames) - 1

                        if save_format == "TIFF":
                            self._save_tiff_frame(
                                save_path,
                                frame_index,
                                result,
                            )

                        if save_format == "HDF5":
                            self._append_hdf5_frame(
                                h5_file,
                                h5_dataset,
                                result,
                            )

                        with self._state_lock:
                            self._finished_count = len(frames)

                        if callback is not None:
                            callback(
                                result
                            )

                    self._event_callback = acquisition_finished

                    self.dev.registerEvent(
                        self.pixet.PX_EVENT_ACQ_FINISHED,
                        0,
                        self._event_callback,
                    )

                rc = self.dev.doSimpleAcquisition(
                    count,
                    measurement_time,
                    pixet_file_type,
                    pixet_file_name,
                )

                if rc != 0:
                    raise RuntimeError(
                        "Acquisition error: " + str(rc)
                    )

                if not need_frame_event:
                    frame_count = self.dev.acqFrameCount()

                    for index in range(frame_count):
                        result = self._read_frame_at(
                            index
                        )

                        frames.append(
                            result
                        )

                    with self._state_lock:
                        self._finished_count = len(frames)

            elif acquisition_type == "Integral":
                rc = self.dev.doSimpleIntegralAcquisition(
                    count,
                    measurement_time,
                    pixet_file_type,
                    pixet_file_name,
                )

                if rc != 0:
                    raise RuntimeError(
                        "Integral acquisition error: " + str(rc)
                    )

                frame_count = self.dev.acqFrameCount()

                if frame_count > 0:
                    result = self._read_last_frame()

                    frames.append(
                        result
                    )

                    if save_format == "TIFF":
                        self._save_tiff_frame(
                            save_path,
                            0,
                            result,
                        )

                    if save_format == "HDF5":
                        self._append_hdf5_frame(
                            h5_file,
                            h5_dataset,
                            result,
                        )

                with self._state_lock:
                    self._finished_count = count

            else:
                raise ValueError(
                    "Unknown acquisition type: "
                    + str(acquisition_type)
                )

            with self._state_lock:
                if self._state == "running":
                    self._state = "finished"

        except Exception as error:
            with self._state_lock:
                if self._state != "aborting":
                    self._state = "error"
                self._last_error = str(error)

            raise

        finally:
            if self._event_callback is not None:
                self.dev.unregisterEvent(
                    self.pixet.PX_EVENT_ACQ_FINISHED,
                    0,
                    self._event_callback,
                )
                self._event_callback = None

            if h5_file is not None:
                h5_file.flush()
                h5_file.close()

        return frames

    def stop(self):
        if not self._started:
            return

        if not self.dev.isAcquisitionRunning():
            return

        with self._state_lock:
            self._state = "aborting"

        self.dev.abortOperation()

    def state(self):
        if not self._started:
            return {
                "state": "closed",
                "running": False,
                "aborting": False,
                "requested_count": self._requested_count,
                "finished_count": self._finished_count,
                "frame_count": 0,
                "last_error": self._last_error,
            }

        running = bool(
            self.dev.isAcquisitionRunning()
        )
        aborting = bool(
            self.dev.isAcquisitionAborting()
        )
        frame_count = self.dev.acqFrameCount()

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
            "frame_count": frame_count,
            "last_error": last_error,
        }

    def is_running(self):
        if not self._started:
            return False

        return bool(
            self.dev.isAcquisitionRunning()
        )

    def is_aborting(self):
        if not self._started:
            return False

        return bool(
            self.dev.isAcquisitionAborting()
        )

    def close(self):
        if self._started:
            if self.dev.isAcquisitionRunning():
                self.stop()

            pypixet.exit()
            self._started = False


# ------------------------------------------------------------
# GUI : Image View
# ------------------------------------------------------------

class ImageView(QGraphicsView):
    def resizeEvent(self, event):
        super().resizeEvent(event)

        items = self.scene().items()

        if len(items) > 0:
            self.fitInView(
                self.scene().itemsBoundingRect(),
                Qt.KeepAspectRatio,
            )


class AcquisitionSignals(QObject):
    frame_ready = pyqtSignal(object)
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)


# ------------------------------------------------------------
# GUI
# ------------------------------------------------------------

class MainWindow(QWidget):
    def __init__(self, mini_pix):
        super().__init__()

        self.mini_pix = mini_pix
        self.frames = []
        self.current_frame_index = 0
        self.image_item = None
        self.acquisition_thread = None
        self.save_path = ""

        self.signals = AcquisitionSignals()
        self.signals.frame_ready.connect(
            self._callback_frame_received
        )
        self.signals.finished.connect(
            self._acquisition_finished
        )
        self.signals.failed.connect(
            self._acquisition_failed
        )

        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle(
            "MiniPIX"
        )

        layout = QVBoxLayout(
            self
        )

        measurement_layout = QHBoxLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem(
            "Counting"
        )
        self.mode_combo.addItem(
            "Energy"
        )

        self.count_spin = QSpinBox()
        self.count_spin.setRange(
            1,
            1000000,
        )
        self.count_spin.setValue(
            COUNT
        )

        self.time_spin = QSpinBox()
        self.time_spin.setRange(
            1,
            86400,
        )
        self.time_spin.setValue(
            TIME
        )
        self.time_spin.setSuffix(
            " s"
        )

        self.acquisition_display_mode = QComboBox()
        self.acquisition_display_mode.addItem(
            "After acquisition"
        )
        self.acquisition_display_mode.addItem(
            "Live callback"
        )

        self.acquisition_type = QComboBox()
        self.acquisition_type.addItem(
            "Frames"
        )
        self.acquisition_type.addItem(
            "Integral"
        )

        self.save_format = QComboBox()
        self.save_format.addItem(
            "None"
        )
        self.save_format.addItem(
            "TIFF"
        )
        self.save_format.addItem(
            "HDF5"
        )
        self.save_format.addItem(
            "PIXet native"
        )

        self.save_path_edit = QLineEdit()
        self.save_path_edit.setReadOnly(
            True
        )

        self.save_path_button = QPushButton(
            "Select..."
        )

        measurement_layout.addWidget(
            QLabel("Mode:")
        )
        measurement_layout.addWidget(
            self.mode_combo
        )
        measurement_layout.addWidget(
            QLabel("Count:")
        )
        measurement_layout.addWidget(
            self.count_spin
        )
        measurement_layout.addWidget(
            QLabel("Time:")
        )
        measurement_layout.addWidget(
            self.time_spin
        )
        measurement_layout.addWidget(
            QLabel("Display:")
        )
        measurement_layout.addWidget(
            self.acquisition_display_mode
        )
        measurement_layout.addWidget(
            QLabel("Acquisition:")
        )
        measurement_layout.addWidget(
            self.acquisition_type
        )
        measurement_layout.addWidget(
            QLabel("Save:")
        )
        measurement_layout.addWidget(
            self.save_format
        )
        measurement_layout.addWidget(
            self.save_path_edit,
            1,
        )
        measurement_layout.addWidget(
            self.save_path_button
        )

        detector_label = QLabel(
            f"Threshold: {THRESHOLD} keV    "
            f"Bias: {BIAS} V    "
            f"Clock: {CLOCK} MHz"
        )

        self.image_view = ImageView()

        # 画像表示領域を固定する場合
        # self.image_view.setFixedSize(768, 768)

        self.image_view.setMinimumSize(
            256,
            256,
        )
        self.image_view.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )
        self.image_view.setAlignment(
            Qt.AlignCenter
        )
        self.image_view.setFrameShape(
            QGraphicsView.NoFrame
        )
        self.image_view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.image_view.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.image_scene = QGraphicsScene()
        self.image_view.setScene(
            self.image_scene
        )

        self.status_label = QLabel(
            "Ready"
        )

        frame_layout = QHBoxLayout()

        self.previous_button = QPushButton(
            "<"
        )

        self.frame_slider = QSlider(
            Qt.Horizontal
        )
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(0)
        self.frame_slider.setValue(0)
        self.frame_slider.setEnabled(False)

        self.next_button = QPushButton(
            ">"
        )

        self.frame_label = QLabel(
            "Frame: - / -"
        )
        self.frame_label.setAlignment(
            Qt.AlignCenter
        )

        frame_layout.addWidget(
            self.previous_button
        )
        frame_layout.addWidget(
            self.frame_slider,
            1,
        )
        frame_layout.addWidget(
            self.next_button
        )
        frame_layout.addWidget(
            self.frame_label
        )

        range_layout = QHBoxLayout()

        self.range_mode = QComboBox()
        self.range_mode.addItem(
            "Auto"
        )
        self.range_mode.addItem(
            "Manual"
        )

        self.range_min = QSpinBox()
        self.range_min.setRange(
            -2147483648,
            2147483647,
        )
        self.range_min.setValue(0)
        self.range_min.setEnabled(False)

        self.range_max = QSpinBox()
        self.range_max.setRange(
            -2147483648,
            2147483647,
        )
        self.range_max.setValue(6)
        self.range_max.setEnabled(False)

        self.interpolation_mode = QComboBox()
        self.interpolation_mode.addItem(
            "Nearest"
        )
        self.interpolation_mode.addItem(
            "Smooth"
        )

        self.range_label = QLabel(
            "Display: Auto"
        )

        range_layout.addWidget(
            QLabel("Range:")
        )
        range_layout.addWidget(
            self.range_mode
        )
        range_layout.addWidget(
            QLabel("Min:")
        )
        range_layout.addWidget(
            self.range_min
        )
        range_layout.addWidget(
            QLabel("Max:")
        )
        range_layout.addWidget(
            self.range_max
        )
        range_layout.addWidget(
            QLabel("Interpolation:")
        )
        range_layout.addWidget(
            self.interpolation_mode
        )
        range_layout.addWidget(
            self.range_label
        )

        self.start_button = QPushButton(
            "Start"
        )

        self.stop_button = QPushButton(
            "Stop"
        )
        self.stop_button.setEnabled(
            False
        )

        start_stop_layout = QHBoxLayout()
        start_stop_layout.addWidget(
            self.start_button
        )
        start_stop_layout.addWidget(
            self.stop_button
        )

        layout.addLayout(
            measurement_layout
        )
        layout.addWidget(
            detector_label
        )
        layout.addWidget(
            self.image_view,
            1,
        )
        layout.addWidget(
            self.status_label
        )
        layout.addLayout(
            frame_layout
        )
        layout.addLayout(
            range_layout
        )
        layout.addLayout(
            start_stop_layout
        )

        self.range_mode.currentIndexChanged.connect(
            self._range_mode_changed
        )
        self.range_min.valueChanged.connect(
            self._display_changed
        )
        self.range_max.valueChanged.connect(
            self._display_changed
        )
        self.interpolation_mode.currentIndexChanged.connect(
            self._display_changed
        )
        self.previous_button.clicked.connect(
            self._show_previous_frame
        )
        self.next_button.clicked.connect(
            self._show_next_frame
        )
        self.frame_slider.valueChanged.connect(
            self._frame_slider_changed
        )
        self.start_button.clicked.connect(
            self._start_acquisition
        )
        self.stop_button.clicked.connect(
            self._stop_acquisition
        )
        self.save_format.currentIndexChanged.connect(
            self._save_format_changed
        )
        self.save_path_button.clicked.connect(
            self._select_save_path
        )
        self.acquisition_type.currentIndexChanged.connect(
            self._acquisition_type_changed
        )

        self._save_format_changed()
        self._acquisition_type_changed()

    def _set_acquisition_controls_enabled(
        self,
        enabled,
    ):
        self.start_button.setEnabled(
            enabled
        )
        self.mode_combo.setEnabled(
            enabled
        )
        self.count_spin.setEnabled(
            enabled
        )
        self.time_spin.setEnabled(
            enabled
        )
        self.acquisition_display_mode.setEnabled(
            enabled
        )
        self.acquisition_type.setEnabled(
            enabled
        )
        self.save_format.setEnabled(
            enabled
        )
        self.save_path_button.setEnabled(
            enabled
        )

        if enabled:
            self.stop_button.setEnabled(
                False
            )
        else:
            self.stop_button.setEnabled(
                True
            )

    def _reset_frames(self):
        self.frames = []
        self.current_frame_index = 0

        self.frame_slider.setEnabled(
            False
        )
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(0)
        self.frame_slider.setValue(0)

        self.frame_label.setText(
            "Frame: - / -"
        )

    def _append_frame(
        self,
        result,
        show_new_frame,
    ):
        self.frames.append(
            result
        )

        self.frame_slider.setMaximum(
            len(self.frames) - 1
        )
        self.frame_slider.setEnabled(
            True
        )

        if show_new_frame:
            self._show_frame(
                len(self.frames) - 1
            )

    def _show_frame(
        self,
        index,
    ):
        if len(self.frames) == 0:
            return

        if index < 0:
            return

        if index >= len(self.frames):
            return

        self.current_frame_index = index
        result = self.frames[
            self.current_frame_index
        ]

        self.frame_label.setText(
            "Frame: "
            + str(self.current_frame_index + 1)
            + " / "
            + str(len(self.frames))
        )

        if self.frame_slider.value() != self.current_frame_index:
            self.frame_slider.blockSignals(
                True
            )
            self.frame_slider.setValue(
                self.current_frame_index
            )
            self.frame_slider.blockSignals(
                False
            )

        self.status_label.setText(
            "Frame: "
            + str(self.current_frame_index + 1)
            + " / "
            + str(len(self.frames))
            + "    Min: "
            + str(result["minimum"])
            + "    Max: "
            + str(result["maximum"])
            + "    Non-zero: "
            + str(result["nonzero"])
        )

        self._show_image(
            result["data"]
        )

    def _show_image(
        self,
        data,
    ):
        if self.range_mode.currentText() == "Auto":
            view_min = float(
                data.min()
            )
            view_max = float(
                data.max()
            )
        else:
            view_min = float(
                self.range_min.value()
            )
            view_max = float(
                self.range_max.value()
            )

        if view_max <= view_min:
            return

        # PIXet GUI と同じ上下方向に合わせる。
        # 元の測定データ自体は変更しない。
        display = np.flipud(
            data
        ).astype(
            np.float64
        ).copy()

        display[
            display < view_min
        ] = view_min
        display[
            display > view_max
        ] = view_max

        display = (
            (display - view_min)
            / (view_max - view_min)
            * 255.0
        ).astype(
            np.uint8
        )

        image = QImage(
            display.data,
            256,
            256,
            display.strides[0],
            QImage.Format_Grayscale8,
        ).copy()

        pixmap = QPixmap.fromImage(
            image
        )

        if self.image_item is None:
            self.image_item = self.image_scene.addPixmap(
                pixmap
            )
        else:
            self.image_item.setPixmap(
                pixmap
            )

        if self.interpolation_mode.currentText() == "Nearest":
            self.image_item.setTransformationMode(
                Qt.FastTransformation
            )
        else:
            self.image_item.setTransformationMode(
                Qt.SmoothTransformation
            )

        self.image_scene.setSceneRect(
            self.image_item.boundingRect()
        )
        self.image_view.fitInView(
            self.image_item,
            Qt.KeepAspectRatio,
        )

        if self.range_mode.currentText() == "Auto":
            self.range_label.setText(
                "Display: Auto  Min="
                + str(view_min)
                + "  Max="
                + str(view_max)
            )
        else:
            self.range_label.setText(
                "Display: Manual  Min="
                + str(view_min)
                + "  Max="
                + str(view_max)
            )

    def _save_format_changed(self):
        save_format = self.save_format.currentText()

        if save_format == "None":
            self.save_path = ""
            self.save_path_edit.setText(
                ""
            )
            self.save_path_button.setEnabled(
                False
            )
        else:
            if self.start_button.isEnabled():
                self.save_path_button.setEnabled(
                    True
                )

    def _select_save_path(self):
        save_format = self.save_format.currentText()

        if save_format == "TIFF":
            path = QFileDialog.getExistingDirectory(
                self,
                "TIFF output directory",
            )

            if path != "":
                self.save_path = path
                self.save_path_edit.setText(
                    path
                )

        elif save_format == "HDF5":
            path, _selected_filter = QFileDialog.getSaveFileName(
                self,
                "HDF5 output file",
                "",
                "HDF5 (*.h5 *.hdf5)",
            )

            if path != "":
                if not path.lower().endswith(
                    (
                        ".h5",
                        ".hdf5",
                    )
                ):
                    path = path + ".h5"

                self.save_path = path
                self.save_path_edit.setText(
                    path
                )

        elif save_format == "PIXet native":
            path, _selected_filter = QFileDialog.getSaveFileName(
                self,
                "PIXet native output file",
                "",
                "PIXet Binary Multi Frame (*.bmf);;"
                "PIXet Multi Frame (*.pmf);;"
                "Pixet Binary Frame (*.pbf)",
            )

            if path != "":
                self.save_path = path
                self.save_path_edit.setText(
                    path
                )

    def _acquisition_type_changed(self):
        if self.acquisition_type.currentText() == "Integral":
            self.acquisition_display_mode.setCurrentText(
                "After acquisition"
            )
            self.acquisition_display_mode.setEnabled(
                False
            )
        else:
            if self.start_button.isEnabled():
                self.acquisition_display_mode.setEnabled(
                    True
                )

    def _start_acquisition(self):
        mode = self.mode_combo.currentText()
        count = self.count_spin.value()
        measurement_time = self.time_spin.value()
        acquisition_type = self.acquisition_type.currentText()
        save_format = self.save_format.currentText()
        save_path = self.save_path

        if save_format != "None":
            if save_path == "":
                self.status_label.setText(
                    "Select save path"
                )
                return

        live_callback = False

        if acquisition_type == "Frames":
            if self.acquisition_display_mode.currentText() == "Live callback":
                live_callback = True

        self._reset_frames()
        self._set_acquisition_controls_enabled(
            False
        )

        if acquisition_type == "Integral":
            self.status_label.setText(
                "Acquiring...  撮像中  Integral"
            )
        else:
            if live_callback:
                self.status_label.setText(
                    "Acquiring...  撮像中  Live callback"
                )
            else:
                self.status_label.setText(
                    "Acquiring...  撮像中  After acquisition"
                )

        try:
            self.mini_pix.configure(
                mode,
                THRESHOLD,
                BIAS,
                CLOCK,
            )
        except Exception as error:
            self._acquisition_failed(
                str(error)
            )
            return

        def run_acquisition():
            try:
                callback = None

                if live_callback:
                    def callback(result):
                        self.signals.frame_ready.emit(
                            result
                        )

                frames = self.mini_pix.acquire(
                    count,
                    measurement_time,
                    acquisition_type,
                    callback,
                    save_format,
                    save_path,
                )

                self.signals.finished.emit(
                    {
                        "frames": frames,
                        "live_callback": live_callback,
                        "acquisition_type": acquisition_type,
                    }
                )

            except Exception as error:
                self.signals.failed.emit(
                    str(error)
                )

        self.acquisition_thread = threading.Thread(
            target=run_acquisition,
            daemon=True,
        )
        self.acquisition_thread.start()

    def _stop_acquisition(self):
        self.status_label.setText(
            "Stopping...  停止処理中"
        )

        try:
            self.mini_pix.stop()
        except Exception as error:
            self.status_label.setText(
                str(error)
            )

    def _callback_frame_received(
        self,
        result,
    ):
        self._append_frame(
            result,
            True,
        )

        self.status_label.setText(
            "Acquiring...  撮像中    Frame: "
            + str(len(self.frames))
        )

    def _acquisition_finished(
        self,
        result,
    ):
        live_callback = result[
            "live_callback"
        ]

        if not live_callback:
            for frame in result["frames"]:
                self._append_frame(
                    frame,
                    False,
                )

            if len(self.frames) > 0:
                self._show_frame(0)

        if live_callback:
            if len(self.frames) > 0:
                self._show_frame(
                    len(self.frames) - 1
                )

        self._set_acquisition_controls_enabled(
            True
        )
        self._save_format_changed()
        self._acquisition_type_changed()

        state = self.mini_pix.state()

        self.status_label.setText(
            "Acquisition ended    State: "
            + str(state["state"])
            + "    Frames: "
            + str(len(self.frames))
        )

    def _acquisition_failed(
        self,
        message,
    ):
        self._set_acquisition_controls_enabled(
            True
        )

        self._save_format_changed()
        self._acquisition_type_changed()

        self.status_label.setText(
            message
        )

    def _show_previous_frame(self):
        if self.current_frame_index <= 0:
            return

        self._show_frame(
            self.current_frame_index - 1
        )

    def _show_next_frame(self):
        if self.current_frame_index >= len(self.frames) - 1:
            return

        self._show_frame(
            self.current_frame_index + 1
        )

    def _frame_slider_changed(
        self,
        value,
    ):
        self._show_frame(
            value
        )

    def _range_mode_changed(self):
        if self.range_mode.currentText() == "Auto":
            self.range_min.setEnabled(
                False
            )
            self.range_max.setEnabled(
                False
            )
        else:
            self.range_min.setEnabled(
                True
            )
            self.range_max.setEnabled(
                True
            )

        self._display_changed()

    def _display_changed(self):
        if len(self.frames) == 0:
            return

        self._show_frame(
            self.current_frame_index
        )


# ------------------------------------------------------------
# 実行
# ------------------------------------------------------------

try:
    mini_pix = MiniPIX()

except Exception as error:
    print(error)
    sys.exit(1)

app = QApplication(
    []
)

window = MainWindow(
    mini_pix
)
window.show()

exit_code = app.exec_()

mini_pix.close()

sys.exit(
    exit_code
)
