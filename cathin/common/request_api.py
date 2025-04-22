import requests


from cathin.common.config import read_port
from loguru import logger

SERVER_START_TIMEOUT = 300  # 5 minutes
SEARCH_TIMEOUT = 10  # 10 seconds


def _call_generate_image_caption_api(cropped_images_base64, prompt="Describe this image."):
    PORT = read_port()
    SERVER_URL = f"http://127.0.0.1:{PORT}"
    GENERATE_CAPTION = f"{SERVER_URL}/generate_image_caption"
    data = {
        'images': cropped_images_base64,
        'prompt': prompt
    }
    response = requests.post(GENERATE_CAPTION, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def _call_classify_image_api(cropped_images_base64):
    PORT = read_port()
    SERVER_URL = f"http://127.0.0.1:{PORT}"
    GENERATE_CAPTION = f"{SERVER_URL}/classify_image"
    payload = {
        'image_base64': cropped_images_base64,
    }
    response = requests.post(GENERATE_CAPTION, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def _call_ocr_api(image_base64):
    PORT = read_port()
    SERVER_URL = f"http://127.0.0.1:{PORT}"
    OCR = f"{SERVER_URL}/perform_ocr"
    data = {
        'image': image_base64,
    }
    response = requests.post(OCR, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None



def _check_service_health():
    PORT = read_port()
    SERVER_URL = f"http://127.0.0.1:{PORT}"
    HEALTH_ENDPOINT = f"{SERVER_URL}/health"
    try:
        response = requests.get(HEALTH_ENDPOINT)
        response.raise_for_status()
        logger.info("Service is running: {}", response.json())
        return True
    except requests.RequestException as e:
        raise Exception("Error checking service health: {}", e)
