import os
import site
import sys

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)

import pypixet
import numpy as np

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QSlider,
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

# Threshold = 5 keV
dev.setThreshold(
    0,
    5.0,
    pixet.PX_THLFLG_ENERGY,
)

# Bias = 150 V
dev.setBias(150.0)

# Clock = 9.66667 MHz
dev.setTimepixClock(9.66667)


# ------------------------------------------------------------
# Qt
# ------------------------------------------------------------

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("MiniPIX")

layout = QVBoxLayout(window)

settings_label = QLabel(
    "Type: Frames    "
    "Mode: Counting    "
    "Count: 100    "
    "Time: 0.1 s\n"
    "Threshold: 5 keV    "
    "Bias: 150 V    "
    "Clock: 9.66667 MHz"
)

image_label = QLabel()
image_label.setFixedSize(768, 768)
image_label.setAlignment(Qt.AlignCenter)

status_label = QLabel("Ready")

range_layout = QHBoxLayout()

range_label = QLabel("View Max: 1")

range_slider = QSlider(Qt.Horizontal)
range_slider.setMinimum(1)
range_slider.setMaximum(100)
range_slider.setValue(1)

range_layout.addWidget(range_label)
range_layout.addWidget(range_slider)

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

    view_max = range_slider.value()

    display = last_data.astype(np.float64).copy()

    display[display < 0] = 0
    display[display > view_max] = view_max

    display = (
        display
        / float(view_max)
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

    range_label.setText(
        "View Max: " + str(view_max)
    )


def range_changed():
    show_image()


range_slider.valueChanged.connect(range_changed)


# ------------------------------------------------------------
# Acquisition
# ------------------------------------------------------------

frame_number = 0


def acquire():
    global frame_number
    global last_data

    if frame_number >= 100:
        start_button.setEnabled(True)
        status_label.setText(
            "Finished - last frame remains displayed"
        )
        return

    rc = dev.doSimpleAcquisition(
        1,
        0.1,
        pixet.PX_FTYPE_NONE,
        "",
    )

    if rc != 0:
        start_button.setEnabled(True)
        status_label.setText(
            "Acquisition error: " + str(rc)
        )
        return

    frame = dev.lastAcqFrameRefInc()

    data = np.array(frame.data())
    data = data.reshape(256, 256)

    last_data = data.copy()

    minimum = data.min()
    maximum = data.max()
    nonzero = np.count_nonzero(data)

    # 実データの最大値に合わせて
    # View Max スライダーの範囲を広げる
    slider_max = int(maximum)

    if slider_max < 10:
        slider_max = 10

    if slider_max > range_slider.maximum():
        range_slider.setMaximum(slider_max)

    show_image()

    frame_number += 1

    status_label.setText(
        "Frame: "
        + str(frame_number)
        + " / 100"
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

    QTimer.singleShot(0, acquire)


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