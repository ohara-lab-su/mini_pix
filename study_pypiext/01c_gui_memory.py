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


def configure_device(pixet, dev):
    pixcfg = dev.pixCfg()

    # Counting
    pixcfg.setModeAll(
        pixet.PX_TPXMODE_MEDIPIX
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


def acquire_frame(pixet, dev):
    """
    MiniPIX から1回測定し、検出器の生フレームを返す。

    GUIには依存しない。
    frame.data() の 256 x 256 pixel 値は変更しない。
    """
    rc = dev.doSimpleAcquisition(
        COUNT,
        TIME,
        pixet.PX_FTYPE_NONE,
        "",
    )

    if rc != 0:
        raise RuntimeError(
            "Acquisition error: " + str(rc)
        )

    frame = dev.lastAcqFrameRefInc()

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
    configure_device(
        pixet,
        dev,
    )

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

settings_label = QLabel(
    f"Type: Frames    "
    "Mode: Counting   "
    f"Count: {COUNT}  "
    f"Time: {TIME} s\n"
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

layout.addWidget(
    settings_label
)

layout.addWidget(
    image_view,
    1,
)

layout.addWidget(
    status_label
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
frame_number = 0


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
    global frame_number
    global last_data

    frame_number = 0

    start_button.setEnabled(
        False
    )

    status_label.setText(
        "Acquiring..."
    )

    QApplication.processEvents()

    try:
        result = acquire_frame(
            pixet,
            dev,
        )

    except Exception as error:
        status_label.setText(
            str(error)
        )

        start_button.setEnabled(
            True
        )

        return

    last_data = result[
        "data"
    ]

    frame_number += 1

    show_image()

    status_label.setText(
        "Frame: "
        + str(frame_number)
        + f" / {COUNT}"
        + "    Min: "
        + str(result["minimum"])
        + "    Max: "
        + str(result["maximum"])
        + "    Non-zero: "
        + str(result["nonzero"])
    )

    print(
        "Frame",
        frame_number,
        "min",
        result["minimum"],
        "max",
        result["maximum"],
        "nonzero",
        result["nonzero"],
    )

    start_button.setEnabled(
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
