import base64

import numpy as np
from cathin.common.request_api import _call_generate_image_caption_api
from cathin.common.utils import _crop_and_encode_image
from flask import Flask, render_template, request, jsonify, send_file

from cathin.console_scripts.cat_ui_web.get_devices import get_android_devices, \
    get_ios_devices
from cathin.console_scripts.cat_ui_web.get_windows import get_win_windows
from cathin.console_scripts.cat_ui_web.screenshot import take_screenshot, \
    process_screenshot

app = Flask(__name__)
import io
from PIL import Image


def get_device_list(platform=None):
    if platform == "Android":
        return get_android_devices()
    elif platform == "iOS":
        return get_ios_devices()
    elif platform == "PC":
        return get_win_windows()
    else:
        return []


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/inspector', methods=['GET'])
def inspector():
    platform = request.args.get('platform')
    device = request.args.get('device')
    language = request.args.get('language')
    # 你可以在这里使用这些参数进行相应的处理
    return render_template('inspector.html', platform=platform, device=device, language=language)


@app.route('/get_description', methods=['POST'])
def get_description():
    bounds = request.json.get('bounds')
    platform = request.json.get('platform')
    device = request.json.get('device')
    language = request.json.get('language')
    img = take_screenshot(platform, device, language)
    bounds = tuple(bounds)
    crop_img = _crop_and_encode_image(img, [bounds])[0]
    text = _call_generate_image_caption_api(crop_img).get("descriptions")
    return jsonify(text)


@app.route('/get_devices', methods=['POST'])
def get_devices():
    platform = request.json.get('platform')
    devices = get_device_list(platform)
    return jsonify(devices)


@app.route('/get_image', methods=['POST'])
def get_image():
    # 从请求中获取参数
    data = request.json
    platform = data.get('platform')
    device = data.get('device')
    language = data.get('language')

    # 获取截图
    img = take_screenshot(platform, device, language)
    new_image, all_values = process_screenshot(img)
    # 检查 img 是否为 numpy.ndarray
    if isinstance(new_image, np.ndarray):
        # 将 numpy.ndarray 转换为 PIL 图像
        new_image = Image.fromarray(new_image.astype('uint8'))

    # 将图像保存到字节流中
    img_io = io.BytesIO()
    new_image.save(img_io, 'PNG')
    img_io.seek(0)

    # 将图像转换为Base64编码
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
    for item in all_values:
        for key, value in item.items():
            item[key] = [int(x) for x in value]

    # 返回图像和文本列表
    return jsonify({
        'image': img_base64,
        'list': all_values,
    })


def main():
    app.run(debug=True, port=5901)
