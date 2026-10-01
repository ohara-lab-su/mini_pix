import os
import site
import sys

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)

import numpy as np
import pypixet

from PyQt5.QtCore import Qt
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

def initialize_device():
    pypixet.start()

    pixet = pypixet.pixet
    devices = pixet.devices()

    if len(devices) == 0:
        pypixet.exit()
        raise RuntimeError("No devices found")

    dev = devices[0]

    print("Device:", dev.fullName())

    return pixet, dev


def configure_device(pixet, dev, mode):
    pixcfg = dev.pixCfg()

    if mode == "Counting":
        pixcfg.setModeAll(
            pixet.PX_TPXMODE_MEDIPIX
        )
    else:
        pixcfg.setModeAll(
            pixet.PX_TPXMODE_TOT
        )

    dev.setThreshold(
        0,
        THRESHOLD,
        pixet.PX_THLFLG_ENERGY,
    )

    dev.setBias(
        BIAS
    )

    dev.setTimepixClock(
        CLOCK
    )


def acquire_frames(pixet, dev, count, measurement_time):
    """
    MiniPIX で COUNT 枚を一括測定し、
    測定終了後に取得された全フレームを返す。

    doSimpleAcquisition() 中は同期的に待機する。
    GUIには依存しない。
    各 frame.data() の 256 x 256 pixel 値は変更しない。
    """
    rc = dev.doSimpleAcquisition(
        count,
        measurement_time,
        pixet.PX_FTYPE_NONE,
        "",
    )

    if rc != 0:
        raise RuntimeError(
            "Acquisition error: " + str(rc)
        )

    frames = []

    for index in range(count):
        frame = dev.acqFrameRefInc(
            index
        )

        try:
            data = np.array(
                frame.data()
            )

            data = data.reshape(
                256,
                256,
            )

            frames.append(
                {
                    "data": data.copy(),
                    "minimum": data.min(),
                    "maximum": data.max(),
                    "nonzero": np.count_nonzero(data),
                }
            )

        finally:
            frame.destroy()

    return frames


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


# ------------------------------------------------------------
# PIXet 初期化
# ------------------------------------------------------------

try:
    pixet, dev = initialize_device()

except Exception as error:
    print(error)
    sys.exit(1)


# ------------------------------------------------------------
# GUI : 構築
# ------------------------------------------------------------

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("MiniPIX")

layout = QVBoxLayout(window)

measurement_layout = QHBoxLayout()

mode_combo = QComboBox()
mode_combo.addItem("Counting")
mode_combo.addItem("Energy")

count_spin = QSpinBox()
count_spin.setRange(
    1,
    1000000,
)
count_spin.setValue(
    COUNT
)

time_spin = QSpinBox()
time_spin.setRange(
    1,
    86400,
)
time_spin.setValue(
    TIME
)
time_spin.setSuffix(
    " s"
)

measurement_layout.addWidget(
    QLabel("Mode:")
)
measurement_layout.addWidget(
    mode_combo
)
measurement_layout.addWidget(
    QLabel("Count:")
)
measurement_layout.addWidget(
    count_spin
)
measurement_layout.addWidget(
    QLabel("Time:")
)
measurement_layout.addWidget(
    time_spin
)
measurement_layout.addStretch()

detector_label = QLabel(
    f"Threshold: {THRESHOLD} keV    "
    f"Bias: {BIAS} V    "
    f"Clock: {CLOCK} MHz"
)

image_view = ImageView()

# 画像表示領域を固定する場合
# image_view.setFixedSize(768, 768)

image_view.setMinimumSize(
    256,
    256,
)

image_view.setSizePolicy(
    QSizePolicy.Expanding,
    QSizePolicy.Expanding,
)

image_view.setAlignment(
    Qt.AlignCenter
)

image_view.setFrameShape(
    QGraphicsView.NoFrame
)

image_view.setHorizontalScrollBarPolicy(
    Qt.ScrollBarAlwaysOff
)

image_view.setVerticalScrollBarPolicy(
    Qt.ScrollBarAlwaysOff
)

image_scene = QGraphicsScene()
image_view.setScene(image_scene)

image_item = None

status_label = QLabel(
    "Ready"
)

frame_layout = QHBoxLayout()

previous_button = QPushButton(
    "<"
)

frame_slider = QSlider(
    Qt.Horizontal
)
frame_slider.setMinimum(0)
frame_slider.setMaximum(0)
frame_slider.setValue(0)
frame_slider.setEnabled(False)

next_button = QPushButton(
    ">"
)

frame_label = QLabel(
    "Frame: - / -"
)
frame_label.setAlignment(
    Qt.AlignCenter
)

frame_layout.addWidget(
    previous_button
)
frame_layout.addWidget(
    frame_slider,
    1,
)
frame_layout.addWidget(
    next_button
)
frame_layout.addWidget(
    frame_label
)

range_layout = QHBoxLayout()

range_mode = QComboBox()
range_mode.addItem("Auto")
range_mode.addItem("Manual")

range_min = QSpinBox()
range_min.setRange(
    -2147483648,
    2147483647,
)
range_min.setValue(0)
range_min.setEnabled(False)

range_max = QSpinBox()
range_max.setRange(
    -2147483648,
    2147483647,
)
range_max.setValue(6)
range_max.setEnabled(False)

interpolation_mode = QComboBox()
interpolation_mode.addItem("Nearest")
interpolation_mode.addItem("Smooth")

range_label = QLabel(
    "Display: Auto"
)

range_layout.addWidget(
    QLabel("Range:")
)
range_layout.addWidget(
    range_mode
)
range_layout.addWidget(
    QLabel("Min:")
)
range_layout.addWidget(
    range_min
)
range_layout.addWidget(
    QLabel("Max:")
)
range_layout.addWidget(
    range_max
)
range_layout.addWidget(
    QLabel("Interpolation:")
)
range_layout.addWidget(
    interpolation_mode
)
range_layout.addWidget(
    range_label
)

start_button = QPushButton(
    "Start"
)

layout.addLayout(
    measurement_layout
)

layout.addWidget(
    detector_label
)

layout.addWidget(
    image_view,
    1,
)

layout.addWidget(
    status_label
)

layout.addLayout(
    frame_layout
)

layout.addLayout(
    range_layout
)

layout.addWidget(
    start_button
)


# ------------------------------------------------------------
# GUI : 表示データ
# ------------------------------------------------------------

last_data = None
acquired_frames = []
current_frame_index = 0


def show_image():
    global image_item

    if last_data is None:
        return

    if range_mode.currentText() == "Auto":
        view_min = float(
            last_data.min()
        )
        view_max = float(
            last_data.max()
        )

    else:
        view_min = float(
            range_min.value()
        )
        view_max = float(
            range_max.value()
        )

    if view_max <= view_min:
        return

    # PIXet GUI と同じ上下方向に合わせる。
    # last_data 自体は変更しない。
    display = np.flipud(
        last_data
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

    if image_item is None:
        image_item = image_scene.addPixmap(
            pixmap
        )

    else:
        image_item.setPixmap(
            pixmap
        )

    if interpolation_mode.currentText() == "Nearest":
        image_item.setTransformationMode(
            Qt.FastTransformation
        )

    else:
        image_item.setTransformationMode(
            Qt.SmoothTransformation
        )

    image_scene.setSceneRect(
        image_item.boundingRect()
    )

    image_view.fitInView(
        image_item,
        Qt.KeepAspectRatio,
    )

    if range_mode.currentText() == "Auto":
        range_label.setText(
            "Display: Auto  Min="
            + str(view_min)
            + "  Max="
            + str(view_max)
        )

    else:
        range_label.setText(
            "Display: Manual  Min="
            + str(view_min)
            + "  Max="
            + str(view_max)
        )


# ------------------------------------------------------------
# GUI : イベント
# ------------------------------------------------------------


def show_frame(index):
    global last_data
    global current_frame_index

    if len(acquired_frames) == 0:
        return

    current_frame_index = index

    result = acquired_frames[
        current_frame_index
    ]

    last_data = result[
        "data"
    ]

    frame_label.setText(
        "Frame: "
        + str(current_frame_index + 1)
        + " / "
        + str(len(acquired_frames))
    )

    if frame_slider.value() != current_frame_index:
        frame_slider.blockSignals(
            True
        )
        frame_slider.setValue(
            current_frame_index
        )
        frame_slider.blockSignals(
            False
        )

    status_label.setText(
        "Frame: "
        + str(current_frame_index + 1)
        + " / "
        + str(len(acquired_frames))
        + "    Min: "
        + str(result["minimum"])
        + "    Max: "
        + str(result["maximum"])
        + "    Non-zero: "
        + str(result["nonzero"])
    )

    show_image()


def show_previous_frame():
    if current_frame_index <= 0:
        return

    show_frame(
        current_frame_index - 1
    )


def show_next_frame():
    if current_frame_index >= len(acquired_frames) - 1:
        return

    show_frame(
        current_frame_index + 1
    )


def frame_slider_changed(value):
    show_frame(
        value
    )

def range_mode_changed():
    if range_mode.currentText() == "Auto":
        range_min.setEnabled(False)
        range_max.setEnabled(False)

    else:
        range_min.setEnabled(True)
        range_max.setEnabled(True)

    show_image()


def display_changed():
    show_image()


def start():
    global acquired_frames
    global current_frame_index

    mode = mode_combo.currentText()
    count = count_spin.value()
    measurement_time = time_spin.value()

    acquired_frames = []
    current_frame_index = 0

    frame_slider.setEnabled(
        False
    )
    frame_slider.setMinimum(0)
    frame_slider.setMaximum(0)
    frame_slider.setValue(0)

    frame_label.setText(
        "Frame: - / -"
    )

    start_button.setEnabled(
        False
    )
    mode_combo.setEnabled(
        False
    )
    count_spin.setEnabled(
        False
    )
    time_spin.setEnabled(
        False
    )

    status_label.setText(
        "Acquiring...  撮像中"
    )

    QApplication.processEvents()

    try:
        configure_device(
            pixet,
            dev,
            mode,
        )

        acquired_frames = acquire_frames(
            pixet,
            dev,
            count,
            measurement_time,
        )

    except Exception as error:
        status_label.setText(
            str(error)
        )

        start_button.setEnabled(
            True
        )
        mode_combo.setEnabled(
            True
        )
        count_spin.setEnabled(
            True
        )
        time_spin.setEnabled(
            True
        )

        return

    if len(acquired_frames) == 0:
        status_label.setText(
            "No frames"
        )

        start_button.setEnabled(
            True
        )
        mode_combo.setEnabled(
            True
        )
        count_spin.setEnabled(
            True
        )
        time_spin.setEnabled(
            True
        )

        return

    frame_slider.setMinimum(0)
    frame_slider.setMaximum(
        len(acquired_frames) - 1
    )
    frame_slider.setValue(0)
    frame_slider.setEnabled(
        True
    )

    show_frame(0)

    print(
        "Acquired frames:",
        len(acquired_frames),
    )

    start_button.setEnabled(
        True
    )
    mode_combo.setEnabled(
        True
    )
    count_spin.setEnabled(
        True
    )
    time_spin.setEnabled(
        True
    )


range_mode.currentIndexChanged.connect(
    range_mode_changed
)

range_min.valueChanged.connect(
    display_changed
)

range_max.valueChanged.connect(
    display_changed
)

interpolation_mode.currentIndexChanged.connect(
    display_changed
)

previous_button.clicked.connect(
    show_previous_frame
)

next_button.clicked.connect(
    show_next_frame
)

frame_slider.valueChanged.connect(
    frame_slider_changed
)

start_button.clicked.connect(
    start
)


# ------------------------------------------------------------
# GUI : 実行
# ------------------------------------------------------------

window.show()

exit_code = app.exec_()

pypixet.exit()

sys.exit(
    exit_code
)
