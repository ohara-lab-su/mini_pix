import sys
import threading

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from pixet_ctrl import MiniPixCtrl


class ImageView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self._scene)

        self._pixmap_item = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)

        self.setAlignment(
            QtCore.Qt.AlignCenter
        )

        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )

        self.setBackgroundBrush(
            QtGui.QBrush(
                QtGui.QColor(0, 0, 0)
            )
        )

    def set_image(
        self,
        image: QtGui.QImage,
        smooth: bool,
    ):
        pixmap = QtGui.QPixmap.fromImage(
            image
        )

        self._pixmap_item.setPixmap(
            pixmap
        )

        if smooth:
            self._pixmap_item.setTransformationMode(
                QtCore.Qt.SmoothTransformation
            )
        else:
            self._pixmap_item.setTransformationMode(
                QtCore.Qt.FastTransformation
            )

        self._scene.setSceneRect(
            self._pixmap_item.boundingRect()
        )

        self._fit_image()

    def _fit_image(self):
        if self._pixmap_item.pixmap().isNull():
            return

        self.fitInView(
            self._pixmap_item,
            QtCore.Qt.KeepAspectRatio,
        )

    def resizeEvent(
        self,
        event,
    ):
        super().resizeEvent(
            event
        )
        self._fit_image()


class ViewSignals(QtCore.QObject):
    frame_received = QtCore.pyqtSignal(object)
    acquisition_finished = QtCore.pyqtSignal(object)
    acquisition_error = QtCore.pyqtSignal(str)


class LocalView(QtWidgets.QMainWindow):
    """
    MiniPixCtrl の完全ローカル動作確認用 VIEW。

    gRPC は使用しない。

    Frames 測定:
        MiniPixCtrl callback から逐次フレームを受信し、
        VIEW 側にも履歴を保持する。

    Integral 測定:
        PIXet 側で積算された最終フレームだけを受信する。

    VIEW 側の self.frames は表示履歴キャッシュであり、
    MiniPixCtrl 内部の測定結果メモリとは別物。
    """

    def __init__(
        self,
        ctrl,
    ):
        super().__init__()

        self.ctrl = ctrl

        self.frames = []
        self.current_index = -1
        self.follow_latest = True

        self.signals = ViewSignals()
        self.signals.frame_received.connect(
            self._on_frame_received
        )
        self.signals.acquisition_finished.connect(
            self._on_acquisition_finished
        )
        self.signals.acquisition_error.connect(
            self._on_acquisition_error
        )

        self._build_ui()

        self.setWindowTitle(
            "MiniPIX Local View"
        )
        self.resize(
            1050,
            800,
        )

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(
            central
        )

        main_layout = QtWidgets.QVBoxLayout(
            central
        )

        control_layout = QtWidgets.QGridLayout()

        self.acquisition_type_combo = QtWidgets.QComboBox()
        self.acquisition_type_combo.addItems(
            [
                "Frames",
                "Integral",
            ]
        )

        self.count_spin = QtWidgets.QSpinBox()
        self.count_spin.setRange(
            1,
            1000000,
        )
        self.count_spin.setValue(
            1
        )

        self.time_spin = QtWidgets.QDoubleSpinBox()
        self.time_spin.setRange(
            0.001,
            1000000.0,
        )
        self.time_spin.setDecimals(
            3
        )
        self.time_spin.setValue(
            1.0
        )
        self.time_spin.setSuffix(
            " s"
        )

        self.start_button = QtWidgets.QPushButton(
            "Start"
        )
        self.stop_button = QtWidgets.QPushButton(
            "Stop"
        )

        self.stop_button.setEnabled(
            False
        )

        self.start_button.clicked.connect(
            self._start_acquisition
        )
        self.stop_button.clicked.connect(
            self._stop_acquisition
        )

        control_layout.addWidget(
            QtWidgets.QLabel("Acquisition"),
            0,
            0,
        )
        control_layout.addWidget(
            self.acquisition_type_combo,
            0,
            1,
        )
        control_layout.addWidget(
            QtWidgets.QLabel("Count"),
            0,
            2,
        )
        control_layout.addWidget(
            self.count_spin,
            0,
            3,
        )
        control_layout.addWidget(
            QtWidgets.QLabel("Time"),
            0,
            4,
        )
        control_layout.addWidget(
            self.time_spin,
            0,
            5,
        )
        control_layout.addWidget(
            self.start_button,
            0,
            6,
        )
        control_layout.addWidget(
            self.stop_button,
            0,
            7,
        )

        main_layout.addLayout(
            control_layout
        )

        display_layout = QtWidgets.QHBoxLayout()

        self.auto_range_check = QtWidgets.QCheckBox(
            "Auto range"
        )
        self.auto_range_check.setChecked(
            True
        )
        self.auto_range_check.stateChanged.connect(
            self._redraw_current
        )

        self.minimum_spin = QtWidgets.QDoubleSpinBox()
        self.minimum_spin.setRange(
            -1000000000.0,
            1000000000.0,
        )
        self.minimum_spin.setDecimals(
            3
        )
        self.minimum_spin.setValue(
            0.0
        )
        self.minimum_spin.valueChanged.connect(
            self._redraw_current
        )

        self.maximum_spin = QtWidgets.QDoubleSpinBox()
        self.maximum_spin.setRange(
            -1000000000.0,
            1000000000.0,
        )
        self.maximum_spin.setDecimals(
            3
        )
        self.maximum_spin.setValue(
            6.0
        )
        self.maximum_spin.valueChanged.connect(
            self._redraw_current
        )

        self.interpolation_combo = QtWidgets.QComboBox()
        self.interpolation_combo.addItems(
            [
                "Nearest",
                "Smooth",
            ]
        )
        self.interpolation_combo.currentIndexChanged.connect(
            self._redraw_current
        )

        display_layout.addWidget(
            self.auto_range_check
        )
        display_layout.addWidget(
            QtWidgets.QLabel("Min")
        )
        display_layout.addWidget(
            self.minimum_spin
        )
        display_layout.addWidget(
            QtWidgets.QLabel("Max")
        )
        display_layout.addWidget(
            self.maximum_spin
        )
        display_layout.addWidget(
            QtWidgets.QLabel("Interpolation")
        )
        display_layout.addWidget(
            self.interpolation_combo
        )
        display_layout.addStretch()

        main_layout.addLayout(
            display_layout
        )

        self.image_view = ImageView()
        main_layout.addWidget(
            self.image_view,
            1,
        )

        history_layout = QtWidgets.QHBoxLayout()

        self.previous_button = QtWidgets.QPushButton(
            "<"
        )
        self.next_button = QtWidgets.QPushButton(
            ">"
        )

        self.frame_slider = QtWidgets.QSlider(
            QtCore.Qt.Horizontal
        )
        self.frame_slider.setRange(
            0,
            0,
        )
        self.frame_slider.setValue(
            0
        )

        self.frame_label = QtWidgets.QLabel(
            "Frame: 0 / 0"
        )

        self.previous_button.clicked.connect(
            self._previous_frame
        )
        self.next_button.clicked.connect(
            self._next_frame
        )
        self.frame_slider.valueChanged.connect(
            self._slider_changed
        )

        history_layout.addWidget(
            self.previous_button
        )
        history_layout.addWidget(
            self.frame_slider,
            1,
        )
        history_layout.addWidget(
            self.next_button
        )
        history_layout.addWidget(
            self.frame_label
        )

        main_layout.addLayout(
            history_layout
        )

        self.status_label = QtWidgets.QLabel(
            "Idle"
        )
        main_layout.addWidget(
            self.status_label
        )

    def _start_acquisition(self):
        if self.ctrl.is_running():
            return

        self.frames = []
        self.current_index = -1
        self.follow_latest = True

        self.frame_slider.blockSignals(
            True
        )
        self.frame_slider.setRange(
            0,
            0,
        )
        self.frame_slider.setValue(
            0
        )
        self.frame_slider.blockSignals(
            False
        )

        self.frame_label.setText(
            "Frame: 0 / 0"
        )

        self.start_button.setEnabled(
            False
        )
        self.stop_button.setEnabled(
            True
        )

        acquisition_type = self.acquisition_type_combo.currentText()
        count = self.count_spin.value()
        sec = self.time_spin.value()

        self.status_label.setText(
            "Running"
        )

        thread = threading.Thread(
            target=self._acquisition_worker,
            args=(
                acquisition_type,
                count,
                sec,
            ),
            daemon=True,
        )
        thread.start()

    def _acquisition_worker(
        self,
        acquisition_type,
        count,
        sec,
    ):
        try:
            if acquisition_type == "Integral":
                result = self.ctrl.acquire_integral(
                    count=count,
                    sec=sec,
                    callback=self._frame_callback,
                )
            else:
                result = self.ctrl.acquire_frames(
                    count=count,
                    sec=sec,
                    callback=self._frame_callback,
                )

            self.signals.acquisition_finished.emit(
                result
            )

        except Exception as error:
            self.signals.acquisition_error.emit(
                str(error)
            )

    def _frame_callback(
        self,
        frame,
    ):
        self.signals.frame_received.emit(
            frame
        )

    def _on_frame_received(
        self,
        frame,
    ):
        self.frames.append(
            frame
        )

        new_index = len(
            self.frames
        ) - 1

        self.frame_slider.blockSignals(
            True
        )
        self.frame_slider.setMaximum(
            new_index
        )

        if self.follow_latest:
            self.current_index = new_index
            self.frame_slider.setValue(
                new_index
            )

        self.frame_slider.blockSignals(
            False
        )

        if self.follow_latest:
            self._display_frame(
                self.current_index
            )
        else:
            self._update_frame_label()

    def _on_acquisition_finished(
        self,
        result,
    ):
        self.start_button.setEnabled(
            True
        )
        self.stop_button.setEnabled(
            False
        )

        state = self.ctrl.state()

        self.status_label.setText(
            "State: "
            + str(state["state"])
            + "    Frames: "
            + str(len(self.frames))
        )

    def _on_acquisition_error(
        self,
        message,
    ):
        self.start_button.setEnabled(
            True
        )
        self.stop_button.setEnabled(
            False
        )

        self.status_label.setText(
            "Error: "
            + message
        )

        QtWidgets.QMessageBox.critical(
            self,
            "Acquisition error",
            message,
        )

    def _stop_acquisition(self):
        try:
            self.ctrl.stop()
            self.status_label.setText(
                "Stopping"
            )
        except Exception as error:
            QtWidgets.QMessageBox.critical(
                self,
                "Stop error",
                str(error),
            )

    def _slider_changed(
        self,
        value,
    ):
        if len(self.frames) == 0:
            return

        self.current_index = int(
            value
        )

        last_index = len(
            self.frames
        ) - 1

        if self.current_index == last_index:
            self.follow_latest = True
        else:
            self.follow_latest = False

        self._display_frame(
            self.current_index
        )

    def _previous_frame(self):
        if len(self.frames) == 0:
            return

        if self.current_index <= 0:
            return

        self.follow_latest = False

        self.frame_slider.setValue(
            self.current_index - 1
        )

    def _next_frame(self):
        if len(self.frames) == 0:
            return

        last_index = len(
            self.frames
        ) - 1

        if self.current_index >= last_index:
            return

        self.frame_slider.setValue(
            self.current_index + 1
        )

    def _redraw_current(self):
        if len(self.frames) == 0:
            return

        if self.current_index < 0:
            return

        self._display_frame(
            self.current_index
        )

    def _display_frame(
        self,
        index,
    ):
        if index < 0:
            return

        if index >= len(self.frames):
            return

        frame = self.frames[
            index
        ]

        data = np.asarray(
            frame["data"]
        )

        # PIXet Pro の表示方向に合わせるための表示専用反転。
        # CTRL 内の raw data は変更しない。
        display_data = np.flipud(
            data
        )

        if self.auto_range_check.isChecked():
            minimum = float(
                np.min(
                    display_data
                )
            )
            maximum = float(
                np.max(
                    display_data
                )
            )
        else:
            minimum = float(
                self.minimum_spin.value()
            )
            maximum = float(
                self.maximum_spin.value()
            )

        if maximum <= minimum:
            maximum = minimum + 1.0

        normalized = (
            display_data.astype(
                np.float64
            )
            - minimum
        )

        normalized = normalized / (
            maximum - minimum
        )

        normalized = np.clip(
            normalized,
            0.0,
            1.0,
        )

        image_data = (
            normalized * 255.0
        ).astype(
            np.uint8
        )

        image_data = np.ascontiguousarray(
            image_data
        )

        height, width = image_data.shape

        image = QtGui.QImage(
            image_data.data,
            width,
            height,
            int(image_data.strides[0]),
            QtGui.QImage.Format_Grayscale8,
        ).copy()

        smooth = False

        if self.interpolation_combo.currentText() == "Smooth":
            smooth = True

        self.image_view.set_image(
            image,
            smooth,
        )

        self._update_frame_label()

        self.status_label.setText(
            "Frame "
            + str(index + 1)
            + "    min="
            + str(frame["minimum"])
            + "    max="
            + str(frame["maximum"])
            + "    nonzero="
            + str(frame["nonzero"])
        )

    def _update_frame_label(self):
        count = len(
            self.frames
        )

        if count == 0:
            self.frame_label.setText(
                "Frame: 0 / 0"
            )
            return

        self.frame_label.setText(
            "Frame: "
            + str(self.current_index + 1)
            + " / "
            + str(count)
        )

    def closeEvent(
        self,
        event,
    ):
        try:
            if self.ctrl.is_running():
                self.ctrl.stop()
        except Exception:
            pass

        try:
            self.ctrl.disconnect()
        finally:
            event.accept()


def main():
    import logging

    logger = logging.getLogger(
        "mini_pix"
    )
    logger.setLevel(
        logging.INFO
    )

    if len(logger.handlers) == 0:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
        handler.setFormatter(
            formatter
        )
        logger.addHandler(
            handler
        )

    ctrl = MiniPixCtrl(
        logger=logger
    )

    if not ctrl.connect():
        raise RuntimeError(
            "MiniPIX connection failed"
        )

    # 動作確認用の固定 detector 設定。
    # GUI から変更しない。
    if not ctrl.set_mode_all(
        "Counting"
    ):
        raise RuntimeError(
            "Failed to set Counting mode"
        )

    if not ctrl.set_threshold(
        2.4
    ):
        raise RuntimeError(
            "Failed to set threshold"
        )

    if not ctrl.set_bias(
        150.0
    ):
        raise RuntimeError(
            "Failed to set bias"
        )

    if not ctrl.set_clock(
        9.66667
    ):
        raise RuntimeError(
            "Failed to set clock"
        )

    app = QtWidgets.QApplication(
        sys.argv
    )

    window = LocalView(
        ctrl
    )
    window.show()

    sys.exit(
        app.exec_()
    )


if __name__ == "__main__":
    main()
