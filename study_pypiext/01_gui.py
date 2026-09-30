import sys

import numpy as np
import pypixet
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# ============================================================
# PIXet 初期化
# ============================================================

print("PIXet start")

pypixet.start()
pixet = pypixet.pixet

devices = pixet.devices()

if len(devices) == 0:
    print("MiniPIX not found")
    pypixet.exit()
    sys.exit(1)

dev = devices[0]

print("Device:", dev.fullName())


# ============================================================
# GUI と同じ測定条件
# ============================================================

COUNT = 100
TIME = 0.1
THRESHOLD = 5.0
BIAS = 150.0
CLOCK = 9.66667


# Counting mode
pixcfg = dev.pixCfg()
rc = pixcfg.setModeAll(pixet.PX_TPXMODE_MEDIPIX)
print("setModeAll Counting:", rc)

# Threshold 5 keV
rc = dev.setThreshold(
    0,
    THRESHOLD,
    pixet.PX_THLFLG_ENERGY,
)
print("setThreshold:", rc)

# Bias 150 V
rc = dev.setBias(BIAS)
print("setBias:", rc)

# Clock 9.66667 MHz
rc = dev.setTimepixClock(CLOCK)
print("setTimepixClock:", rc)

print()
print("Actual settings")
print("Threshold:", dev.threshold(0, pixet.PX_THLFLG_ENERGY), "keV")
print("Bias     :", dev.bias(), "V")
print("Clock    :", dev.timepixClock(), "MHz")
print()


# ============================================================
# Qt GUI
# ============================================================

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("MiniPIX Simple Viewer")

layout = QVBoxLayout(window)

settings_label = QLabel(
    "Type: Frames    "
    "Mode: Counting    "
    "Count: 100    "
    "Time: 0.1 s\n"
    "Threshold: 5 keV    "
    "Bias: 150 V    "
    "Clock: 9.66667 MHz    "
    "Range: Min-Max"
)

image_label = QLabel()
image_label.setFixedSize(768, 768)
image_label.setAlignment(Qt.AlignCenter)

status_label = QLabel("Ready")

start_button = QPushButton("Start")

layout.addWidget(settings_label)
layout.addWidget(image_label)
layout.addWidget(status_label)
layout.addWidget(start_button)

window.show()


# ============================================================
# 測定
# ============================================================

frame_number = 0

timer = QTimer()


def acquire_frame():
    global frame_number

    if frame_number >= COUNT:
        timer.stop()
        start_button.setEnabled(True)
        status_label.setText("Finished")
        return

    rc = dev.doSimpleAcquisition(
        1,
        TIME,
        pixet.PX_FTYPE_NONE,
        "",
    )

    if rc != 0:
        timer.stop()
        start_button.setEnabled(True)

        status_label.setText(
            "Acquisition error: "
            + str(rc)
            + " "
            + dev.lastError()
        )
        return

    frame = dev.lastAcqFrameRefInc()

    data = np.array(
        frame.data(),
        dtype=np.float64,
    )

    data = data.reshape(256, 256)

    minimum = data.min()
    maximum = data.max()

    # Auto Range: Min-Max
    display = np.zeros(
        (256, 256),
        dtype=np.uint8,
    )

    if maximum > minimum:
        display = (
            (data - minimum)
            / (maximum - minimum)
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
        image_label.size(),
        Qt.KeepAspectRatio,
        Qt.FastTransformation,
    )

    image_label.setPixmap(pixmap)

    frame_number += 1

    status_label.setText(
        "Frame: "
        + str(frame_number)
        + " / "
        + str(COUNT)
        + "    Min: "
        + str(minimum)
        + "    Max: "
        + str(maximum)
        + "    Non-zero: "
        + str(np.count_nonzero(data))
    )

    print(
        "Frame",
        frame_number,
        "min",
        minimum,
        "max",
        maximum,
        "nonzero",
        np.count_nonzero(data),
    )

    frame.destroy()

    # 次のフレーム
    QTimer.singleShot(0, acquire_frame)


def start():
    global frame_number

    frame_number = 0

    start_button.setEnabled(False)
    status_label.setText("Acquiring...")

    acquire_frame()


start_button.clicked.connect(start)


# ============================================================
# 終了
# ============================================================

exit_code = app.exec_()

pypixet.exit()

sys.exit(exit_code)