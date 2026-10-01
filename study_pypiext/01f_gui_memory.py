import os
import site
import sys
import threading

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)

import numpy as np
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
    PIXet / MiniPIX の初期化、設定、測定、終了処理を担当する。

    GUI には依存しない。
    callback=None の場合は測定終了後に全フレームを返す。
    callback を指定した場合は各フレーム測定完了時に callback(frame) を呼ぶ。
    """

    def __init__(self):
        self.pixet = None
        self.dev = None
        self._started = False
        self._event_callback = None

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

    def acquire(
        self,
        count,
        measurement_time,
        callback=None,
    ):
        """
        count 枚を測定する共通API。

        callback=None:
            doSimpleAcquisition() 完了後に全フレームを読み出して返す。

        callback指定:
            PX_EVENT_ACQ_FINISHED を登録し、各フレーム完了時に
            callback(frame_result) を呼ぶ。
            doSimpleAcquisition() 自体は同期APIなので、このメソッドを
            GUIスレッド以外から呼べばGUIはブロックされない。
        """
        frames = []

        if callback is not None:
            def acquisition_finished(_count):
                result = self._read_last_frame()
                frames.append(
                    result
                )
                callback(
                    result
                )

            self._event_callback = acquisition_finished

            self.dev.registerEvent(
                self.pixet.PX_EVENT_ACQ_FINISHED,
                0,
                self._event_callback,
            )

        try:
            rc = self.dev.doSimpleAcquisition(
                count,
                measurement_time,
                self.pixet.PX_FTYPE_NONE,
                "",
            )

            if rc != 0:
                raise RuntimeError(
                    "Acquisition error: " + str(rc)
                )

            if callback is None:
                for index in range(count):
                    frames.append(
                        self._read_frame_at(
                            index
                        )
                    )

        finally:
            if self._event_callback is not None:
                self.dev.unregisterEvent(
                    self.pixet.PX_EVENT_ACQ_FINISHED,
                    0,
                    self._event_callback,
                )
                self._event_callback = None

        return frames

    def close(self):
        if self._started:
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
        measurement_layout.addStretch()

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
        layout.addWidget(
            self.start_button
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

    def _start_acquisition(self):
        mode = self.mode_combo.currentText()
        count = self.count_spin.value()
        measurement_time = self.time_spin.value()

        live_callback = False
        if self.acquisition_display_mode.currentText() == "Live callback":
            live_callback = True

        self._reset_frames()
        self._set_acquisition_controls_enabled(
            False
        )

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
                    callback,
                )

                self.signals.finished.emit(
                    {
                        "frames": frames,
                        "live_callback": live_callback,
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

        self.status_label.setText(
            "Acquisition finished    Frames: "
            + str(len(self.frames))
        )

    def _acquisition_failed(
        self,
        message,
    ):
        self._set_acquisition_controls_enabled(
            True
        )

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
    sys.argv
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
