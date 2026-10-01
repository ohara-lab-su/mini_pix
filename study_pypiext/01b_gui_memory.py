import os
import site
import sys

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)

import pypixet
import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)


pypixet.start()
pixet = pypixet.pixet

devices = pixet.devices()

if len(devices) == 0:
    print("No devices found")
    pypixet.exit()
    sys.exit(1)

dev = devices[0]

print("Device:", dev.fullName())


# ------------------------------------------------------------
# GUI と同じ設定
# ------------------------------------------------------------

pixcfg = dev.pixCfg()

# Counting
pixcfg.setModeAll(pixet.PX_TPXMODE_MEDIPIX)

TIME = 1
COUNT = 1

THRESHOLD = 2.4
BIAS = 150.0
CLOCK = 9.66667

# Threshold = 5 keV
dev.setThreshold(
    0,
    THRESHOLD,
    pixet.PX_THLFLG_ENERGY,
)

# Bias = 150 V
dev.setBias(BIAS)

# Clock = 9.66667 MHz
dev.setTimepixClock(CLOCK)


# ------------------------------------------------------------
# Qt
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

image_label = QLabel()
image_label.setFixedSize(768, 768)
image_label.setAlignment(Qt.AlignCenter)

status_label = QLabel("Ready")

range_layout = QHBoxLayout()

range_mode_label = QLabel("Range:")

range_mode = QComboBox()
range_mode.addItem("Auto")
range_mode.addItem("Manual")

range_min_label = QLabel("Min:")

range_min = QSpinBox()
range_min.setRange(-2147483648, 2147483647)
range_min.setValue(0)
range_min.setEnabled(False)

range_max_label = QLabel("Max:")

range_max = QSpinBox()
range_max.setRange(-2147483648, 2147483647)
range_max.setValue(6)
range_max.setEnabled(False)

range_value_label = QLabel("Display: Auto")

range_layout.addWidget(range_mode_label)
range_layout.addWidget(range_mode)
range_layout.addWidget(range_min_label)
range_layout.addWidget(range_min)
range_layout.addWidget(range_max_label)
range_layout.addWidget(range_max)
range_layout.addWidget(range_value_label)

start_button = QPushButton("Start")

layout.addWidget(settings_label)
layout.addWidget(image_label)
layout.addWidget(status_label)
layout.addLayout(range_layout)
layout.addWidget(start_button)

window.show()


# ------------------------------------------------------------
# 表示
# ------------------------------------------------------------

last_data = None


def show_image():
    if last_data is None:
        return

    if range_mode.currentText() == "Auto":
        view_min = float(last_data.min())
        view_max = float(last_data.max())
    else:
        view_min = float(range_min.value())
        view_max = float(range_max.value())

    if view_max <= view_min:
        return

    display = last_data.astype(np.float64).copy()

    display[display < view_min] = view_min
    display[display > view_max] = view_max

    display = (
        (display - view_min)
        / (view_max - view_min)
        * 255.0
    ).astype(np.uint8)

    image = QImage(
        display.data,
        256,
        256,
        display.strides[0],
        QImage.Format_Grayscale8,
    ).copy()

    pixmap = QPixmap.fromImage(image)

    pixmap = pixmap.scaled(
        image_label.width(),
        image_label.height(),
        Qt.KeepAspectRatio,
        Qt.FastTransformation,
    )

    image_label.setPixmap(pixmap)

    if range_mode.currentText() == "Auto":
        range_value_label.setText(
            "Display: Auto  Min="
            + str(view_min)
            + "  Max="
            + str(view_max)
        )
    else:
        range_value_label.setText(
            "Display: Manual  Min="
            + str(view_min)
            + "  Max="
            + str(view_max)
        )


def range_mode_changed():
    if range_mode.currentText() == "Auto":
        range_min.setEnabled(False)
        range_max.setEnabled(False)
    else:
        range_min.setEnabled(True)
        range_max.setEnabled(True)

    show_image()


def range_changed():
    show_image()


range_mode.currentIndexChanged.connect(range_mode_changed)
range_min.valueChanged.connect(range_changed)
range_max.valueChanged.connect(range_changed)


# ------------------------------------------------------------
# Acquisition
# ------------------------------------------------------------

frame_number = 0


def acquire():
    global frame_number
    global last_data

    ###################################
    rc = dev.doSimpleAcquisition(
        COUNT,
        TIME,
        pixet.PX_FTYPE_NONE,
        "",
    )
    ###################################

    if rc != 0:
        start_button.setEnabled(True)
        status_label.setText(
            "Acquisition error: " + str(rc)
        )
        return

    frame = dev.lastAcqFrameRefInc()

    ###################################
    data = np.array(frame.data())
    data = data.reshape(256, 256)

    last_data = data.copy()

    minimum = data.min()
    maximum = data.max()
    nonzero = np.count_nonzero(data)

    show_image()

    frame_number += 1

    status_label.setText(
        "Frame: "
        + str(frame_number)
        + f" / {COUNT}"
        + "    Min: "
        + str(minimum)
        + "    Max: "
        + str(maximum)
        + "    Non-zero: "
        + str(nonzero)
    )

    print(
        "Frame",
        frame_number,
        "min",
        minimum,
        "max",
        maximum,
        "nonzero",
        nonzero,
    )

    frame.destroy()

    start_button.setEnabled(True)


def start():
    global frame_number

    frame_number = 0

    start_button.setEnabled(False)
    status_label.setText("Acquiring...")

    acquire()


start_button.clicked.connect(start)


# ------------------------------------------------------------
# GUI
# ------------------------------------------------------------

exit_code = app.exec_()

pypixet.exit()

sys.exit(exit_code)