import base64
import json

import cv2
import cv2 as cv
import numpy as np
import requests

camera_matrix = np.array([[1612.59872732951, -0.322499171177306, 1265.18659717837],
                          [0., 1612.15199437803, 708.874191354349],
                          [0., 0., 1.]])

dist_coeffs = np.array(
    [[-0.443947590101190],
     [0.245002940770680],
     [-0.000682381695366930],
     [-0.00127148900702161],
     [-0.0734141582733169]])

image_size = (2560, 1440)
# image_size = (1920, 1080)

map1, map2 = cv2.initUndistortRectifyMap(camera_matrix, dist_coeffs, None, None, image_size, cv2.CV_32FC1)

services = ['target_pic', 'base_pic', 'classify_pic']
detection_server_ip = 'http://114.212.85.141:2627'


def post_with_callback(resp_func, image, device_id, service_type=0, url=detection_server_ip):
    payload = {
        "device": device_id,
        "time": "2022-1-1",
        "image_type": service_type,  # 0 target 1 base 2 classify
        "image_format": "jpg",
        "image_size": "",
        "image_data": ""
    }

    _, img_bytes = cv.imencode('.jpg', image)
    img_64 = base64.b64encode(img_bytes).decode()
    payload['image_data'] = img_64
    payload['image_size'] = len(img_bytes)

    requests.post(f'{url}/{services[service_type]}', json=payload, hooks={'response': resp_func})

    # return json.loads(resp.text)


def post_with_block(image, device_id, service_type=0, url=detection_server_ip):
    payload = {
        "device": device_id,
        "time": "2022-1-1",
        "image_type": service_type,  # 0 target 1 base 2 classify
        "image_format": "jpg",
        "image_size": "",
        "image_data": ""
    }

    _, img_bytes = cv.imencode('.jpg', image)
    img_64 = base64.b64encode(img_bytes).decode()
    payload['image_data'] = img_64
    payload['image_size'] = len(img_bytes)

    resp = requests.post(f'{url}/{services[service_type]}', json=payload)

    return json.loads(resp.text)


# BUTTON_STYLE = """
#         QPushButton {
#             background-color: #3e8ed0;
#             color: #fff;
#             border-style: outset;
#             border-width: 2px;
#             border-radius: 10px;
#             border-color: transparent;
#             padding: 8px;
#             font:0.25em;
#             min-height: 15;
#             max-width: 400;
#             min-width: 200;
#         }
#         QPushButton:hover {
#             background-color: #3e8ed0;
#         }
#         QPushButton:hover:!pressed {
#             border-width: 2px;
#         }
#         QPushButton:hover:pressed {
#             border-width: 3px;
#         }
#         """
BUTTON_STYLE = """
        QPushButton {
            padding: 8px;
            font:0.25em;
            min-height: 20;
            max-width: 400;
            min-width: 200;
        }
        """

monitor_btn_text_map = {
    0: "开始监控",
    1: "暂停监控"
}

benchmark_btn_text_map = {
    1: "上传基准图",
    3: "更新基准图",
    2: "正在上传"
}

detect_btn_text_map = {
    1: "开始检测",
    2: "暂停检测"
}

ipList = {
    0: "rtsp://admin:rinc123456@192.168.1.62:554/h264",
    1: "rtsp://admin:l1234567@192.168.1.63:554/h264",
    2: "rtmp://192.168.1.66/live/livestream",
    # 2: 0  # "rtsp://admin:welcome2rinc@192.168.1.64:554/h264"
}
