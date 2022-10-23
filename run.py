import json
import sys
from dataclasses import dataclass

from PyQt5.QtWidgets import (
    QWidget,
    QApplication, QVBoxLayout
)

from util import monitor_btn_text_map, post_with_callback, benchmark_btn_text_map, post_with_block, detect_btn_text_map
from widgets import QHLine, ControllerView, MainView


@dataclass
class Status:
    monitor_status = 0  # 0: 无监视；1：正在监视
    benchmark_status = -1  # 1：无上传；3：已上传；2：正在上传
    detect_status = -1  # 1: 无检测；2 ：已检测；

    monitor_btn_text = "开始监控"
    benchmark_btn_text = "更新基准图"
    detect_btn_text = "开始检测"

    def next(self, type_str):
        if type_str == "monitor":
            self.monitor_status = 0 if self.monitor_status == 1 else 1
            self.monitor_btn_text = monitor_btn_text_map[self.monitor_status]
        if type_str == "benchmark":
            if self.benchmark_status < 0:
                self.benchmark_status = - self.benchmark_status
            else:
                if self.benchmark_status == 1 or self.benchmark_status == 3:
                    self.benchmark_status = 2
                elif self.benchmark_status == 2:
                    self.benchmark_status = 3
                    if self.detect_status < 0:
                        self.detect_status = - self.detect_status
                        self.detect_btn_text = detect_btn_text_map[self.detect_status]
            self.benchmark_btn_text = benchmark_btn_text_map[self.benchmark_status]

        if type_str == "detect":
            if self.detect_status < 0:
                self.detect_status = - self.detect_status
            else:
                if self.detect_status == 1:
                    self.detect_status = 2
                elif self.detect_status == 2:
                    self.detect_status = 1
            self.detect_btn_text = detect_btn_text_map[self.detect_status]


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.state = [Status() for _ in range(3)]
        self.device_id = 0

        layout = QVBoxLayout()

        controller = ControllerView(self.device_id, self.state[self.device_id])
        controller.combo_box.currentIndexChanged.connect(self.on_device_changed)
        controller.m_button.clicked.connect(self.monitor_click)
        controller.i_button.clicked.connect(self.upload_click)
        controller.d_button.clicked.connect(self.detect_click)

        self.controller = controller

        main_view = MainView()
        for device in main_view.content.devices:
            device.is_open.connect(self.on_monitor_open)

        self.main_view = main_view

        layout.addWidget(main_view)
        layout.addWidget(QHLine())
        layout.addWidget(controller)

        self.setLayout(layout)

        desktop = QApplication.desktop()
        self.setMinimumHeight(int(desktop.height() * 0.8))

    def on_device_changed(self, value):
        self.device_id = value
        status = self.state[self.device_id]
        self.controller.setup(status)

    def monitor_click(self):
        status = self.state[self.device_id]
        status.next("monitor")

        if status.monitor_status == 0:
            status.benchmark_status = -1
            status.detect_status = -1
            self.controller.setup(status)
            self.main_view.content.devices[self.device_id].frame_worker.turn_off()
        else:
            self.controller.setup(status)
            self.main_view.content.devices[self.device_id].frame_worker.turn_on()

    def detect_click(self):
        status = self.state[self.device_id]
        status.next("detect")

        if status.detect_status == 2:
            self.controller.setup(status)
            self.main_view.content.devices[self.device_id].detect_worker.turn_on()
        elif status.detect_status == 1:
            self.controller.setup(status)
            self.main_view.content.devices[self.device_id].detect_worker.turn_off()

    def detect_task(self, device_id):
        while True:
            image = self.main_view.content.devices[device_id].image
            ret = post_with_block(image, device_id, 0)
            if ret['code'] == 0:
                assert int(ret["device"]) == device_id
                labels = ret["labels"]
                self.main_view.content.devices[device_id].set_detect(image, labels)

    def upload_click(self):
        status = self.state[self.device_id]
        status.next("benchmark")
        self.controller.setup(status)
        self.controller.i_button.setEnabled(False)
        image = self.main_view.content.devices[self.device_id].image
        post_with_callback(self.upload_hook_generate(image), image, self.device_id, 1)

    def upload_hook_generate(self, image):
        device_id = self.device_id

        def on_upload_success(resp, *args, **kwargs):
            ret = json.loads(resp.text)
            print(ret)
            if ret['code'] == 0:
                self.main_view.content.devices[device_id].set_benchmark(image)
                status = self.state[device_id]
                status.next("benchmark")
                self.controller.setup(status)

        return on_upload_success

    def on_monitor_open(self, device_id, is_open):
        status = self.state[device_id]
        if status.benchmark_status < 0:
            status.next("benchmark")
        if self.device_id == device_id:
            self.controller.setup(status)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
