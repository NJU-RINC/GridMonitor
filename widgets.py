from typing import List

import cv2
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QSize
from PyQt5.QtGui import (
    QFont, QImage, QPixmap, QColor,
)
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QLabel, QFrame, QComboBox, QPushButton,
)

from util import BUTTON_STYLE
from worker import FrameWorker, DetectWorker


class MonitorLabel(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()

        qf = QFont("Microsoft YaHei", 14, 75)
        for text in "监视", "基准", "检测":
            label = QLabel(text)
            label.setFont(qf)
            label.setStyleSheet("background-color: white")
            label.setFixedWidth(300)
            label.setFixedHeight(34)
            label.setAlignment(Qt.AlignHCenter)
            layout.addWidget(label, alignment=Qt.AlignHCenter)

        self.setLayout(layout)
        self.setFixedHeight(40)


class DeviceLabel(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        qf = QFont("Microsoft YaHei", 10, 75)
        for i in range(3):
            label = QLabel(f"{i + 1}号设备:")
            label.setFont(qf)
            label.setFixedWidth(120)
            layout.addWidget(label, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.setFixedWidth(130)


class FrameLabel(QWidget):
    def __init__(self):
        super(FrameLabel, self).__init__()
        layout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setScaledContents(True)
        self.image_label.setFixedWidth(400)
        self.image_label.setFixedHeight(300)
        self.clear_label()
        # self.image_label.setStyleSheet("""
        # QLabel{
        #     border: 2px solid white;
        # }
        # """)

        layout.addWidget(self.image_label, alignment=Qt.AlignVCenter)

        self.setLayout(layout)

    def set_pixmap(self, rgb_image):
        if rgb_image is None:
            self.clear_label()
        else:
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_qt_format.scaled(640, 480, Qt.KeepAspectRatio)
            self.image_label.setPixmap(QPixmap.fromImage(p))

    def clear_label(self):
        pixmap = QPixmap(QSize(640, 480))
        pixmap.fill(QColor(0, 0, 0))
        self.image_label.setPixmap(pixmap)


class Device(QWidget):
    defect_type = {
        1: "GKXGW"
    }

    is_open = pyqtSignal(int, bool)

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id
        self.image = None
        self.setup_ui()
        self.setup_worker()

    # noinspection PyAttributeOutsideInit
    def setup_ui(self):
        self.realtime = FrameLabel()  # 监视视图
        self.benchmark = FrameLabel()  # 基准图
        self.result = FrameLabel()  # 检测视图

        layout = QHBoxLayout()  # 水平布局
        layout.addWidget(self.realtime, alignment=Qt.AlignHCenter)
        layout.addWidget(self.benchmark, alignment=Qt.AlignHCenter)
        layout.addWidget(self.result, alignment=Qt.AlignHCenter)

        self.setLayout(layout)
        # self.setFixedHeight(420)

    # noinspection PyAttributeOutsideInit
    def setup_worker(self):
        self.frame_worker = FrameWorker(self.device_id)
        self.frame_worker.frame.connect(self.set_image)
        self.frame_worker.start()

        self.detect_worker = DetectWorker(self)
        self.detect_worker.start()

    @pyqtSlot(object)
    def set_image(self, rgb_image: np.array):
        self.realtime.set_pixmap(rgb_image)
        if rgb_image is not None and self.image is None:
            self.is_open.emit(self.device_id, True)
        self.image = rgb_image

    def set_benchmark(self, image):
        self.benchmark.set_pixmap(image)

    def set_detect(self, image, labels: List[dict]):
        for label in labels:
            cls = label['cls']
            w = label['w']
            h = label['h']
            x = label['x']
            y = label['y']
            height, width, channel = image.shape
            left_top = (int(x * width), int(y * height))
            right_bottom = (int((x + w) * width), int((y + h) * height))
            image = cv2.rectangle(image, left_top, right_bottom, (255, 0, 0), 3)
            cv2.putText(image, cls, left_top, cv2.QT_FONT_NORMAL, 4, (255, 0, 0), 2, cv2.LINE_AA)

        self.result.set_pixmap(image)


class Content(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    # noinspection PyAttributeOutsideInit
    def setup_ui(self):
        # 创建布局
        layout = QVBoxLayout()
        layout.setSpacing(0)

        m_label = MonitorLabel()
        m_label.setFixedHeight(50)

        # 向布局里添加部件
        layout.addWidget(m_label)
        self.devices = []
        for i in range(3):
            self.devices.append(Device(i))
            layout.addWidget(self.devices[i], alignment=Qt.AlignVCenter)

        # 应用窗口顶级布局
        self.setLayout(layout)


class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class MainView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("国网demo")
        self.resize(2000, 1260)
        self.content = Content()
        layout = QHBoxLayout()
        layout.addWidget(DeviceLabel())
        layout.addWidget(self.content)

        self.setLayout(layout)


class ControllerView(QWidget):
    state_chg = pyqtSignal(int, str, int)

    def __init__(self, device_id, status):
        super().__init__()

        combo_box = QComboBox()
        combo_box.addItems([f"设备{i + 1}" for i in range(3)])
        combo_box.setFixedWidth(130)
        combo_box.setStyleSheet("""
            QComboBox {
                font:0.5em;
                min-height: 30;
            }
        """)
        combo_box.setCurrentIndex(device_id)
        self.combo_box = combo_box

        m_button = QPushButton()
        m_button.setStyleSheet(BUTTON_STYLE)
        self.m_button = m_button

        i_button = QPushButton()
        i_button.setStyleSheet(BUTTON_STYLE)
        i_button.setEnabled(False)
        self.i_button = i_button

        d_button = QPushButton()
        d_button.setStyleSheet(BUTTON_STYLE)
        d_button.setEnabled(False)
        self.d_button = d_button

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(combo_box, alignment=Qt.AlignLeft)
        layout.addWidget(m_button, alignment=Qt.AlignLeft)
        layout.addWidget(i_button, alignment=Qt.AlignLeft)
        layout.addWidget(d_button, alignment=Qt.AlignLeft)

        self.setLayout(layout)
        self.setFixedHeight(50)
        self.setup(status)

    def setup(self, status):
        self.m_button.setText(status.monitor_btn_text)
        if status.benchmark_status < 0:
            self.i_button.setEnabled(False)
        else:
            self.i_button.setEnabled(True)
        self.i_button.setText(status.benchmark_btn_text)
        if status.detect_status < 0:
            self.d_button.setEnabled(False)
        else:
            self.d_button.setEnabled(True)
        self.d_button.setText(status.detect_btn_text)
