"""
MiniPIX callback acquisition GUI test.

01b_gui_memory.py と同じ測定パラメーター構成で、
1回の doSimpleAcquisition(COUNT, TIME, PX_FTYPE_NONE, "") に対して
PX_EVENT_ACQ_FINISHED callback で各フレームを受け取り、GUI表示する。
"""

######################################################
import os
import site
import sys
import threading
import queue

pixet_dir = r"C:\opt\ese774\modules\API_PIXet_Pro_1.8.3_Windows_x86_64"

# Python 3.7 では add_dll_directory は使えないため PATH を変更
os.environ["PATH"] = pixet_dir + ";" + os.environ["PATH"]
site.addsitedir(pixet_dir)
######################################################

import numpy as np
import pypixet

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QSlider,
    QVBoxLayout,
    QWidget,
)


# ==========================================================
# PIXet Core / MiniPIX 初期化
# ==========================================================

print("pixet core init...")

pypixet.start()
pixet = pypixet.pixet

devices = pixet.devices()

if len(devices) == 0:
    pypixet.exit()
    raise RuntimeError("No devices found")

dev = devices[0]

print("device:")
print("  fullName :", dev.fullName())
print("  deviceType:", dev.deviceType())
print("  chipType  :", dev.chipType())


# ==========================================================
# Timepix 設定
# ==========================================================

pixcfg = dev.pixCfg()

pixcfg.setModeAll(
    pixet.PX_TPXMODE_MEDIPIX,
)

TIME = 1
COUNT = 100

THRESHOLD = 2.4
BIAS = 150.0
CLOCK = 9.66667

dev.setThreshold(
    0,
    THRESHOLD,
    pixet.PX_THLFLG_ENERGY,
)

dev.setBias(BIAS)
dev.setTimepixClock(CLOCK)


# ==========================================================
# callback -> GUI 間の受け渡し
# ==========================================================

frame_queue = queue.Queue()

acq_finished = False
acq_rc = None
received_count = 0


def callback_acq_finished(cnt):
    """
    1フレームの acquisition 完了ごとに PIXet Core から呼ばれる。

    callback 内では GUI を直接操作せず、
    最新フレームをコピーして queue に渡すだけにする。
    """
    global received_count

    frame = dev.lastAcqFrameRefInc()

    if frame is None:
        return

    try:
        data = np.array(
            frame.data(),
            dtype=np.float64,
            copy=True,
        ).reshape(256, 256)
    finally:
        frame.destroy()

    received_count += 1
    frame_queue.put((received_count, data))


def acquisition_worker():
    """
    PIXet の blocking acquisition を GUI スレッドとは別に実行する。
    """
    global acq_finished
    global acq_rc

    print("register PX_EVENT_ACQ_FINISHED")

    dev.registerEvent(
        pixet.PX_EVENT_ACQ_FINISHED,
        0,
        callback_acq_finished,
    )

    try:
        print(
            "doSimpleAcquisition({}, {}, PX_FTYPE_NONE, '') - start".format(
                COUNT,
                TIME,
            )
        )

        acq_rc = dev.doSimpleAcquisition(
            COUNT,
            TIME,
            pixet.PX_FTYPE_NONE,
            "",
        )

        print(
            "doSimpleAcquisition - end:",
            acq_rc,
            "(0 is OK)",
        )

    finally:
        dev.unregisterEvent(
            pixet.PX_EVENT_ACQ_FINISHED,
            0,
            callback_acq_finished,
        )

        acq_finished = True


# ==========================================================
# Qt GUI
# ==========================================================

app = QApplication(sys.argv)

window = QMainWindow()
window.setWindowTitle("MiniPIX 01c GUI Callback")

central = QWidget()
layout = QVBoxLayout(central)

image_label = QLabel()
image_label.setAlignment(Qt.AlignCenter)
image_label.setMinimumSize(512, 512)

status_label = QLabel("Waiting for acquisition...")

view_max_label = QLabel("View Max: 10")

view_max_slider = QSlider(Qt.Horizontal)
view_max_slider.setMinimum(1)
view_max_slider.setMaximum(255)
view_max_slider.setValue(10)

layout.addWidget(image_label)
layout.addWidget(status_label)
layout.addWidget(view_max_label)
layout.addWidget(view_max_slider)

window.setCentralWidget(central)
window.resize(620, 700)

last_data = None
last_frame_number = 0


def draw_frame():
    """
    最後に受信したフレームを現在の View Max で描画する。
    """
    if last_data is None:
        return

    view_max = view_max_slider.value()

    display = last_data.astype(np.float64).copy()

    display[display < 0] = 0
    display[display > view_max] = view_max

    display = (
        display / float(view_max) * 255.0
    ).astype(np.uint8)

    display = np.ascontiguousarray(display)

    height, width = display.shape

    image = QImage(
        display.data,
        width,
        height,
        display.strides[0],
        QImage.Format_Grayscale8,
    ).copy()

    pixmap = QPixmap.fromImage(image)
    pixmap = pixmap.scaled(
        512,
        512,
        Qt.KeepAspectRatio,
        Qt.FastTransformation,
    )

    image_label.setPixmap(pixmap)


def update_view_max(value):
    view_max_label.setText(
        "View Max: {}".format(value)
    )
    draw_frame()


def update_gui():
    """
    callback が queue に入れたフレームを Qt メインスレッドで表示する。

    GUI が一時的に遅れても、queue 内のフレームは順番に保持される。
    """
    global last_data
    global last_frame_number

    updated = False

    while True:
        try:
            frame_number, data = frame_queue.get_nowait()
        except queue.Empty:
            break

        last_frame_number = frame_number
        last_data = data
        updated = True

    if updated:
        draw_frame()

        status_label.setText(
            "Frame: {}/{}".format(last_frame_number, COUNT)
        )

    if acq_finished:
        if frame_queue.empty():
            status_label.setText(
                "Finished: {}/{} frames, rc={}".format(
                    last_frame_number,
                    COUNT,
                    acq_rc,
                )
            )


view_max_slider.valueChanged.connect(update_view_max)

timer = QTimer()
timer.timeout.connect(update_gui)
timer.start(20)

window.show()


# ==========================================================
# acquisition 開始
# ==========================================================

worker = threading.Thread(
    target=acquisition_worker,
    daemon=True,
)
worker.start()


# ==========================================================
# Qt 実行
# ==========================================================

exit_code = app.exec_()

worker.join()

pypixet.exit()

sys.exit(exit_code)
