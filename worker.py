import time
from threading import Lock, Condition

import cv2
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QImage

from util import map1, map2, ipList, post_with_block


class FrameWorker(QThread):
    frame = pyqtSignal([object], [type(None)])

    def __init__(self, device_id):
        super(FrameWorker, self).__init__()
        self.url = ipList[device_id]
        self.lock = Lock()
        self.cond = Condition(self.lock)
        self.open = False
        self.device_id = device_id

    def run(self):
        cap = cv2.VideoCapture(self.url)
        # cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        while True:
            with self.cond:
                while not self.open:
                    self.frame[type(None)].emit(None)
                    self.cond.wait()

            success, frame = cap.read()

            while not success:
                print('try')
                cap = cv2.VideoCapture(self.url)
                success, frame = cap.read()

            if success:
                if self.device_id != 2:
                    frame = cv2.remap(frame, map1, map2, cv2.INTER_LINEAR)
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.frame[object].emit(rgb_image)
            time.sleep(1/fps)

    def turn_on(self):
        with self.cond:
            self.open = True
            self.cond.notify()

    def turn_off(self):
        with self.cond:
            self.open = False


class DetectWorker(QThread):
    def __init__(self, device):
        super(DetectWorker, self).__init__()
        self.device = device
        self.lock = Lock()
        self.cond = Condition(self.lock)
        self.open = False

    def run(self):
        while True:
            with self.cond:
                while not self.open:
                    self.device.result.clear_label()
                    self.device.result.clear_label()
                    self.cond.wait()
            image = self.device.image
            ret = post_with_block(image, self.device.device_id, 0)
            if ret['code'] == 0:
                assert int(ret["device"]) == self.device.device_id
                labels = ret["labels"]
                self.device.set_detect(image, labels)

    def turn_on(self):
        with self.cond:
            self.open = True
            self.cond.notify()

    def turn_off(self):
        with self.cond:
            self.open = False
