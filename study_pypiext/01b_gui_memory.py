import os
import site
import sys

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)

import pypixet
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
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

figure = Figure(figsize=(7.68, 7.68), dpi=100)
figure.subplots_adjust(left=0, right=1, bottom=0, top=1)

image_canvas = FigureCanvasQTAgg(figure)
image_canvas.setFixedSize(768, 768)

image_axes = figure.add_subplot(111)
image_axes.set_axis_off()

image_plot = None

status_label = QLabel("Ready")

start_button = QPushButton("Start")

layout.addWidget(settings_label)
layout.addWidget(image_canvas)
layout.addWidget(status_label)
layout.addWidget(start_button)

window.show()


# ------------------------------------------------------------
# 表示
# ------------------------------------------------------------

last_data = None


def show_image():
    global image_plot

    if last_data is None:
        return

    if image_plot is None:
        image_plot = image_axes.imshow(
            last_data,
            cmap="gray",
            vmin=0,
            vmax=6,
            interpolation="nearest",
            origin="upper",
        )
    else:
        image_plot.set_data(last_data)
        image_plot.set_clim(0, 6)

    image_canvas.draw_idle()


# ------------------------------------------------------------
# Acquisition
# ------------------------------------------------------------

def acquire():
    global last_data

    start_button.setEnabled(False)
    status_label.setText("Acquiring...")

    rc = dev.doSimpleAcquisition(
        COUNT,
        TIME,
        pixet.PX_FTYPE_NONE,
        "",
    )

    if rc != 0:
        start_button.setEnabled(True)
        status_label.setText("Acquisition error: " + str(rc))
        return

    frame_count = dev.acqFrameCount()

    for frame_number in range(frame_count):
        frame = dev.acqFrameRefInc(frame_number)

        try:
            data = np.asarray(frame.data()).reshape(256, 256)

            # 生データをそのまま保持する。値変換は一切しない。
            last_data = data

            minimum = data.min()
            maximum = data.max()
            nonzero = np.count_nonzero(data)

            print(
                "Frame",
                frame_number + 1,
                "/",
                frame_count,
                "dtype",
                data.dtype,
                "shape",
                data.shape,
                "min",
                minimum,
                "max",
                maximum,
                "nonzero",
                nonzero,
            )

            show_image()
            QApplication.processEvents()

            status_label.setText(
                "Frame: "
                + str(frame_number + 1)
                + " / "
                + str(frame_count)
                + "    dtype: "
                + str(data.dtype)
                + "    Min: "
                + str(minimum)
                + "    Max: "
                + str(maximum)
                + "    Non-zero: "
                + str(nonzero)
            )

        finally:
            frame.destroy()

    start_button.setEnabled(True)


def start():
    acquire()


start_button.clicked.connect(start)


# ------------------------------------------------------------
# GUI
# ------------------------------------------------------------

exit_code = app.exec_()

pypixet.exit()

sys.exit(exit_code)
