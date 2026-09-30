import os
import site
import sys
import threading

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
window.setWindowTitle("MiniPIX callback")

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
latest_frame_number = 0
latest_minimum = 0
latest_maximum = 0
latest_nonzero = 0
acquisition_running = False
acquisition_finished = False
acquisition_rc = None
data_lock = threading.Lock()


def callback_acq_finished(cnt):
    global frame_number
    global last_data
    global latest_frame_number
    global latest_minimum
    global latest_maximum
    global latest_nonzero

    frame = dev.lastAcqFrameRefInc()

    if frame is None:
        print("callback: frame is None")
        return

    try:
        data = np.array(frame.data())
        data = data.reshape(256, 256)
        data = data.copy()

        minimum = data.min()
        maximum = data.max()
        nonzero = np.count_nonzero(data)

        frame_number += 1

        with data_lock:
            last_data = data
            latest_frame_number = frame_number
            latest_minimum = minimum
            latest_maximum = maximum
            latest_nonzero = nonzero

        print(
            "Callback",
            frame_number,
            "cnt",
            cnt,
            "min",
            minimum,
            "max",
            maximum,
            "nonzero",
            nonzero,
        )

    finally:
        frame.destroy()


def acquisition_worker():
    global acquisition_running
    global acquisition_finished
    global acquisition_rc

    dev.registerEvent(
        pixet.PX_EVENT_ACQ_FINISHED,
        0,
        callback_acq_finished,
    )

    try:
        acquisition_rc = dev.doSimpleAcquisition(
            COUNT,
            TIME,
            pixet.PX_FTYPE_NONE,
            "",
        )
    finally:
        dev.unregisterEvent(
            pixet.PX_EVENT_ACQ_FINISHED,
            0,
            callback_acq_finished,
        )

        acquisition_running = False
        acquisition_finished = True


def update_gui():
    global acquisition_finished

    with data_lock:
        data = last_data
        current_frame_number = latest_frame_number
        minimum = latest_minimum
        maximum = latest_maximum
        nonzero = latest_nonzero

    if data is not None:
        slider_max = int(maximum)

        if slider_max < 10:
            slider_max = 10

        if slider_max > range_slider.maximum():
            range_slider.setMaximum(slider_max)

        show_image()

        status_label.setText(
            "Frame: "
            + str(current_frame_number)
            + " / "
            + str(COUNT)
            + "    Min: "
            + str(minimum)
            + "    Max: "
            + str(maximum)
            + "    Non-zero: "
            + str(nonzero)
        )

    if acquisition_finished:
        acquisition_finished = False

        if acquisition_rc != 0:
            status_label.setText(
                "Acquisition error: " + str(acquisition_rc)
            )
        else:
            status_label.setText(
                "Finished - "
                + str(current_frame_number)
                + " frames"
            )

        start_button.setEnabled(True)


def start():
    global frame_number
    global last_data
    global latest_frame_number
    global acquisition_running
    global acquisition_finished
    global acquisition_rc

    if acquisition_running:
        return

    frame_number = 0
    latest_frame_number = 0
    acquisition_finished = False
    acquisition_rc = None

    with data_lock:
        last_data = None

    start_button.setEnabled(False)
    status_label.setText("Acquiring...")

    acquisition_running = True

    worker = threading.Thread(
        target=acquisition_worker,
        daemon=True,
    )
    worker.start()


start_button.clicked.connect(start)

timer = QTimer()
timer.timeout.connect(update_gui)
timer.start(20)


# ------------------------------------------------------------
# GUI
# ------------------------------------------------------------

exit_code = app.exec_()

pypixet.exit()

sys.exit(exit_code)