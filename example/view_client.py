#!/usr/bin/env python3
import asyncio
import sys
import threading

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from mini_pix.config import Config
from mini_pix.server_grpc import AsyncPixetGrpcClient
from x_logger import XLogger


class ImageView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self._scene)

        self._pixmap_item = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)

        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        self.setBackgroundBrush(
            QtGui.QBrush(QtGui.QColor(0, 0, 0))
        )

    def set_image(
        self,
        image: QtGui.QImage,
        smooth: bool,
    ):
        pixmap = QtGui.QPixmap.fromImage(image)
        self._pixmap_item.setPixmap(pixmap)

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_image()


class ViewSignals(QtCore.QObject):
    frame_received = QtCore.pyqtSignal(object)
    acquisition_finished = QtCore.pyqtSignal()
    acquisition_error = QtCore.pyqtSignal(str)


class ClientView(QtWidgets.QMainWindow):
    """
    MiniPIX gRPC VIEW client。

    サーバーから送られる逐次フレームを VIEW クライアント側の frames に蓄積する。
    したがって測定中も測定後も、受信済み履歴を slider / < / > で閲覧できる。
    """

    def __init__(
        self,
        config,
        logger,
    ):
        super().__init__()

        self.config = config
        self.logger = logger

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

        self.setWindowTitle("MiniPIX Client View")
        self.resize(1050, 800)

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        main_layout = QtWidgets.QVBoxLayout(central)

        control_layout = QtWidgets.QGridLayout()

        self.acquisition_type_combo = QtWidgets.QComboBox()
        self.acquisition_type_combo.addItems(
            [
                "Frames",
                "Integral",
            ]
        )

        self.count_spin = QtWidgets.QSpinBox()
        self.count_spin.setRange(1, 1000000)
        self.count_spin.setValue(1)

        self.time_spin = QtWidgets.QDoubleSpinBox()
        self.time_spin.setRange(0.001, 1000000.0)
        self.time_spin.setDecimals(3)
        self.time_spin.setValue(1.0)
        self.time_spin.setSuffix(" s")

        self.start_button = QtWidgets.QPushButton("Start")
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.setEnabled(False)

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

        main_layout.addLayout(control_layout)

        display_layout = QtWidgets.QHBoxLayout()

        self.auto_range_check = QtWidgets.QCheckBox(
            "Auto range"
        )
        self.auto_range_check.setChecked(True)
        self.auto_range_check.stateChanged.connect(
            self._redraw_current
        )

        self.minimum_spin = QtWidgets.QDoubleSpinBox()
        self.minimum_spin.setRange(
            -1000000000.0,
            1000000000.0,
        )
        self.minimum_spin.setDecimals(3)
        self.minimum_spin.setValue(0.0)
        self.minimum_spin.valueChanged.connect(
            self._redraw_current
        )

        self.maximum_spin = QtWidgets.QDoubleSpinBox()
        self.maximum_spin.setRange(
            -1000000000.0,
            1000000000.0,
        )
        self.maximum_spin.setDecimals(3)
        self.maximum_spin.setValue(6.0)
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

        display_layout.addWidget(self.auto_range_check)
        display_layout.addWidget(QtWidgets.QLabel("Min"))
        display_layout.addWidget(self.minimum_spin)
        display_layout.addWidget(QtWidgets.QLabel("Max"))
        display_layout.addWidget(self.maximum_spin)
        display_layout.addWidget(
            QtWidgets.QLabel("Interpolation")
        )
        display_layout.addWidget(self.interpolation_combo)
        display_layout.addStretch()

        main_layout.addLayout(display_layout)

        self.image_view = ImageView()
        main_layout.addWidget(self.image_view, 1)

        history_layout = QtWidgets.QHBoxLayout()

        self.previous_button = QtWidgets.QPushButton("<")
        self.next_button = QtWidgets.QPushButton(">")

        self.frame_slider = QtWidgets.QSlider(
            QtCore.Qt.Horizontal
        )
        self.frame_slider.setRange(0, 0)
        self.frame_slider.setValue(0)

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

        history_layout.addWidget(self.previous_button)
        history_layout.addWidget(self.frame_slider, 1)
        history_layout.addWidget(self.next_button)
        history_layout.addWidget(self.frame_label)

        main_layout.addLayout(history_layout)

        self.status_label = QtWidgets.QLabel("Idle")
        main_layout.addWidget(self.status_label)

    def _start_acquisition(self):
        self.frames = []
        self.current_index = -1
        self.follow_latest = True

        self.frame_slider.blockSignals(True)
        self.frame_slider.setRange(0, 0)
        self.frame_slider.setValue(0)
        self.frame_slider.blockSignals(False)

        self.frame_label.setText("Frame: 0 / 0")

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Running")

        acquisition_type = (
            self.acquisition_type_combo.currentText()
        )
        count = self.count_spin.value()
        sec = self.time_spin.value()

        thread = threading.Thread(
            target=self._stream_worker,
            args=(
                acquisition_type,
                count,
                sec,
            ),
            daemon=True,
        )
        thread.start()

    def _stream_worker(
        self,
        acquisition_type,
        count,
        sec,
    ):
        try:
            asyncio.run(
                self._stream_acquisition(
                    acquisition_type,
                    count,
                    sec,
                )
            )
            self.signals.acquisition_finished.emit()

        except Exception as error:
            self.signals.acquisition_error.emit(
                str(error)
            )

    async def _stream_acquisition(
        self,
        acquisition_type,
        count,
        sec,
    ):
        client = AsyncPixetGrpcClient(
            server_ip=self.config.SERVER_IP,
            server_port=self.config.SERVER_PORT,
            set_timeout_sec=None,
            logger=self.logger,
            log_level=self.config.LOGGER_LEVEL,
        )

        await client.connect()

        try:
            await client.set_mode_all("Counting")
            await client.set_threshold(2.4)
            await client.set_bias(150.0)
            await client.set_clock(9.66667)

            if acquisition_type == "Integral":
                async for frame in client.stream_integral(
                    count,
                    sec,
                ):
                    self.signals.frame_received.emit(
                        frame
                    )
            else:
                async for frame in client.stream_frames(
                    count,
                    sec,
                ):
                    self.signals.frame_received.emit(
                        frame
                    )

        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    def _stop_acquisition(self):
        self.status_label.setText("Stopping")

        thread = threading.Thread(
            target=self._stop_worker,
            daemon=True,
        )
        thread.start()

    def _stop_worker(self):
        try:
            asyncio.run(self._stop_remote())
        except Exception as error:
            self.signals.acquisition_error.emit(
                str(error)
            )

    async def _stop_remote(self):
        client = AsyncPixetGrpcClient(
            server_ip=self.config.SERVER_IP,
            server_port=self.config.SERVER_PORT,
            set_timeout_sec=self.config.TIMEOUT,
            logger=self.logger,
            log_level=self.config.LOGGER_LEVEL,
        )

        await client.connect()

        try:
            await client.stop()
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    def _on_frame_received(self, frame):
        self.frames.append(frame)

        new_index = len(self.frames) - 1

        self.frame_slider.blockSignals(True)
        self.frame_slider.setMaximum(new_index)

        if self.follow_latest:
            self.current_index = new_index
            self.frame_slider.setValue(new_index)

        self.frame_slider.blockSignals(False)

        if self.follow_latest:
            self._display_frame(self.current_index)
        else:
            self._update_frame_label()

    def _on_acquisition_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self.status_label.setText(
            "Finished    Frames: "
            + str(len(self.frames))
        )

    def _on_acquisition_error(self, message):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self.status_label.setText(
            "Error: " + message
        )

        QtWidgets.QMessageBox.critical(
            self,
            "Acquisition error",
            message,
        )

    def _slider_changed(self, value):
        if len(self.frames) == 0:
            return

        self.current_index = int(value)

        last_index = len(self.frames) - 1

        if self.current_index == last_index:
            self.follow_latest = True
        else:
            self.follow_latest = False

        self._display_frame(self.current_index)

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

        last_index = len(self.frames) - 1

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

        self._display_frame(self.current_index)

    def _display_frame(self, index):
        if index < 0:
            return

        if index >= len(self.frames):
            return

        frame = self.frames[index]
        data = np.asarray(frame["data"])

        display_data = np.flipud(data)

        if self.auto_range_check.isChecked():
            minimum = float(np.min(display_data))
            maximum = float(np.max(display_data))
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
            display_data.astype(np.float64)
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
        ).astype(np.uint8)
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

        if (
            self.interpolation_combo.currentText()
            == "Smooth"
        ):
            smooth = True

        self.image_view.set_image(
            image,
            smooth,
        )

        self._update_frame_label()

        minimum_value = frame.get("minimum")
        maximum_value = frame.get("maximum")
        nonzero = frame.get("nonzero")

        self.status_label.setText(
            "Frame "
            + str(index + 1)
            + "    min="
            + str(minimum_value)
            + "    max="
            + str(maximum_value)
            + "    nonzero="
            + str(nonzero)
        )

    def _update_frame_label(self):
        count = len(self.frames)

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


def main():
    config = Config("mini_pix.yaml")

    logger = XLogger(
        log_level=config.LOGGER_LEVEL,
        logger_name=config.CLIENT_LOGGER_NAME,
    )

    app = QtWidgets.QApplication(sys.argv)

    window = ClientView(
        config,
        logger,
    )
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
