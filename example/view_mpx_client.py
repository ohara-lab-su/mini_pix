#!/usr/bin/env python3
import asyncio

import numpy as np
import pygui

from mini_pix.config import Config
from mini_pix.server_grpc import AsyncPixetGrpcClient
from x_logger import XLogger


TOPIC_NAME = "minipix.frame"


class MpxClientView:
    """
    gRPC で受信した MiniPIX フレームを PIXet の MpxFramePanel で表示する。

    このクライアントは PIXet の Python GUI API (pygui) 上で動作させる。
    フレーム表示には MpxFramePanel を使用し、Auto range、Color map、
    Grid、Rotate、Under/Over warning、Save image は PIXet 側の機能を使う。
    """

    def __init__(
        self,
        config,
        logger,
    ):
        self.config = config
        self.logger = logger

        self.frames = []
        self.current_index = -1
        self.stop_requested = False

        self.window = pygui.MainWindow()
        self.window.setTitle(
            "MiniPIX Mpx Client View"
        )
        self.window.setSize(
            1050,
            800,
        )

        self._build_ui()
        self.window.show()

    def _build_ui(self):
        self.frame_panel = self.window.MpxFramePanel()
        self.frame_panel.setMinimumSize(
            768,
            640,
        )
        self.frame_panel.keepAspectRatio(
            True
        )
        self.frame_panel.showColorBar(
            True
        )
        self.frame_panel.showAxis(
            True
        )
        self.frame_panel.showSaveButton(
            True
        )
        self.frame_panel.showGridButton(
            True
        )
        self.frame_panel.showRotateButton(
            True
        )
        self.frame_panel.showAutoRangeButton(
            True
        )
        self.frame_panel.showColorMapButton(
            True
        )
        self.frame_panel.showUnderButton(
            True
        )
        self.frame_panel.showOverButton(
            True
        )
        self.frame_panel.setAutoRange(
            True
        )

        self.acquisition_type_label = self.window.Label(
            "Acquisition"
        )
        self.acquisition_type_combo = self.window.ComboBox()
        self.acquisition_type_combo.setItems(
            [
                "Frames",
                "Integral",
            ]
        )

        self.count_label = self.window.Label(
            "Count"
        )
        self.count_spin = self.window.SpinBox()
        self.count_spin.setMinimum(
            1
        )
        self.count_spin.setMaximum(
            1000000
        )
        self.count_spin.setValue(
            1
        )

        self.time_label = self.window.Label(
            "Time [s]"
        )
        self.time_spin = self.window.DoubleSpinBox()
        self.time_spin.setMinimum(
            0.001
        )
        self.time_spin.setMaximum(
            1000000.0
        )
        self.time_spin.setValue(
            1.0
        )

        self.start_button = self.window.Button(
            "Start"
        )
        self.stop_button = self.window.Button(
            "Stop"
        )
        self.stop_button.setEnabled(
            False
        )

        self.previous_button = self.window.Button(
            "<"
        )
        self.next_button = self.window.Button(
            ">"
        )
        self.frame_label = self.window.Label(
            "Frame: 0 / 0"
        )
        self.status_label = self.window.Label(
            "Idle"
        )

        self.start_button.clicked = self._start_acquisition
        self.stop_button.clicked = self._stop_acquisition
        self.previous_button.clicked = self._previous_frame
        self.next_button.clicked = self._next_frame

        control_layout = self.window.newGridLayout()
        control_layout.addWidget(
            self.acquisition_type_label,
            0,
            0,
            1,
            1,
        )
        control_layout.addWidget(
            self.acquisition_type_combo,
            0,
            1,
            1,
            1,
        )
        control_layout.addWidget(
            self.count_label,
            0,
            2,
            1,
            1,
        )
        control_layout.addWidget(
            self.count_spin,
            0,
            3,
            1,
            1,
        )
        control_layout.addWidget(
            self.time_label,
            0,
            4,
            1,
            1,
        )
        control_layout.addWidget(
            self.time_spin,
            0,
            5,
            1,
            1,
        )
        control_layout.addWidget(
            self.start_button,
            0,
            6,
            1,
            1,
        )
        control_layout.addWidget(
            self.stop_button,
            0,
            7,
            1,
            1,
        )

        control_box = self.window.GroupBox()
        control_box.setTitle(
            "Acquisition"
        )
        control_box.setLayout(
            control_layout
        )

        history_layout = self.window.newGridLayout()
        history_layout.addWidget(
            self.previous_button,
            0,
            0,
            1,
            1,
        )
        history_layout.addWidget(
            self.frame_label,
            0,
            1,
            1,
            1,
        )
        history_layout.addWidget(
            self.next_button,
            0,
            2,
            1,
            1,
        )

        history_box = self.window.GroupBox()
        history_box.setTitle(
            "Frame history"
        )
        history_box.setLayout(
            history_layout
        )

        main_layout = self.window.newGridLayout()
        main_layout.addWidget(
            control_box,
            0,
            0,
            1,
            1,
        )
        main_layout.addWidget(
            self.frame_panel,
            1,
            0,
            1,
            1,
        )
        main_layout.addWidget(
            history_box,
            2,
            0,
            1,
            1,
        )
        main_layout.addWidget(
            self.status_label,
            3,
            0,
            1,
            1,
        )
        main_layout.setRowStretch(
            1,
            1,
        )

        self.window.setLayout(
            main_layout
        )

    def _new_client(
        self,
        timeout,
    ):
        return AsyncPixetGrpcClient(
            server_ip=self.config.SERVER_IP,
            server_port=self.config.SERVER_PORT,
            set_timeout_sec=timeout,
            logger=self.logger,
            log_level=self.config.LOGGER_LEVEL,
        )

    def _start_acquisition(self):
        self.frames = []
        self.current_index = -1
        self.stop_requested = False

        self.start_button.setEnabled(
            False
        )
        self.stop_button.setEnabled(
            True
        )
        self.status_label.setText(
            "Running"
        )
        self.frame_label.setText(
            "Frame: 0 / 0"
        )
        self.window.processEvents()

        acquisition_type = self.acquisition_type_combo.currentText()
        count = self.count_spin.value()
        sec = self.time_spin.value()

        try:
            asyncio.run(
                self._run_remote(
                    acquisition_type,
                    count,
                    sec,
                )
            )

            if self.stop_requested:
                self.status_label.setText(
                    "Stopped    Frames: "
                    + str(
                        len(
                            self.frames
                        )
                    )
                )
            else:
                self.status_label.setText(
                    "Finished    Frames: "
                    + str(
                        len(
                            self.frames
                        )
                    )
                )

        except Exception as error:
            self.status_label.setText(
                "Error: "
                + str(
                    error
                )
            )
            pygui.showError(
                "Acquisition error",
                str(
                    error
                ),
            )

        self.start_button.setEnabled(
            True
        )
        self.stop_button.setEnabled(
            False
        )
        self.window.processEvents()

    async def _run_remote(
        self,
        acquisition_type,
        count,
        sec,
    ):
        client = self._new_client(
            None
        )

        await client.set_mode_all(
            "Counting"
        )
        await client.set_threshold(
            2.4
        )
        await client.set_bias(
            150.0
        )
        await client.set_clock(
            9.66667
        )

        stream_method = "acquire_frames"

        if acquisition_type == "Integral":
            stream_method = "acquire_integral"

        for frame in client.stream_call(
            stream_method,
            count,
            sec,
        ):
            if self.stop_requested:
                break

            self._on_frame_received(
                frame
            )
            self.window.processEvents()

    def _stop_acquisition(self):
        if self.stop_requested:
            return

        self.stop_requested = True
        self.status_label.setText(
            "Stopping"
        )
        self.window.processEvents()

        try:
            asyncio.run(
                self._stop_remote()
            )
        except Exception as error:
            self.status_label.setText(
                "Stop error: "
                + str(
                    error
                )
            )
            pygui.showError(
                "Stop error",
                str(
                    error
                ),
            )

    async def _stop_remote(self):
        client = self._new_client(
            self.config.TIMEOUT
        )

        await client.stop()

    def _on_frame_received(
        self,
        frame,
    ):
        if not isinstance(
            frame,
            dict,
        ):
            return

        if "data" not in frame:
            return

        self.frames.append(
            frame
        )
        self.current_index = len(
            self.frames
        ) - 1

        self._display_frame(
            self.current_index
        )

    def _display_frame(
        self,
        index,
    ):
        if index < 0:
            return

        if index >= len(
            self.frames
        ):
            return

        frame = self.frames[
            index
        ]

        data = np.asarray(
            frame["data"]
        )

        if data.ndim != 2:
            raise ValueError(
                "Frame data must be a 2-dimensional array."
            )

        height = int(
            data.shape[0]
        )
        width = int(
            data.shape[1]
        )

        frame_data = np.ascontiguousarray(
            data
        ).reshape(
            -1
        ).tolist()

        self.frame_panel.setData(
            frame_data,
            width,
            height,
        )

        self._update_frame_label()

        self.status_label.setText(
            "Frame "
            + str(
                index + 1
            )
            + "    min="
            + str(
                frame.get(
                    "minimum"
                )
            )
            + "    max="
            + str(
                frame.get(
                    "maximum"
                )
            )
            + "    nonzero="
            + str(
                frame.get(
                    "nonzero"
                )
            )
        )

        self.window.processEvents()

    def _previous_frame(self):
        if self.current_index <= 0:
            return

        self.current_index -= 1
        self._display_frame(
            self.current_index
        )

    def _next_frame(self):
        if len(
            self.frames
        ) == 0:
            return

        last_index = len(
            self.frames
        ) - 1

        if self.current_index >= last_index:
            return

        self.current_index += 1
        self._display_frame(
            self.current_index
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
            + str(
                self.current_index + 1
            )
            + " / "
            + str(
                count
            )
        )


def main():
    config = Config(
        "mini_pix.yaml"
    )

    logger = XLogger(
        log_level=config.LOGGER_LEVEL,
        logger_name=config.CLIENT_LOGGER_NAME,
    )

    MpxClientView(
        config,
        logger,
    )


if __name__ == "__main__":
    main()
