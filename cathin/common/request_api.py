import subprocess
import time
from loguru import logger
import requests
import json
import socket

from cathin.common.config import read_port, get_config_file_path, update_port


SERVER_START_TIMEOUT = 300  # 5 minutes
SEARCH_TIMEOUT = 10  # 10 seconds


def _call_generate_image_caption_api(cropped_images_base64, prompt="The image shows"):
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


def __create_port(new_port):
    config_file_path = get_config_file_path()
    config = {'port': new_port}
    with open(config_file_path, 'w') as file:
        json.dump(config, file, indent=4)


def __check_service_health(index=0):
    PORT = read_port()
    SERVER_URL = f"http://127.0.0.1:{PORT}"
    HEALTH_ENDPOINT = f"{SERVER_URL}/health"
    try:
        response = requests.get(HEALTH_ENDPOINT)
        response.raise_for_status()
        logger.info("Service is running: {}", response.json())
        return True
    except requests.RequestException as e:
        if index == 0:
            logger.error("Error checking service health: {}", e)
        elif index == 1:
            logger.error("Wait for the service to start, it may take 2-3 minutes depending on performance", e)
        return False


def __is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def __find_available_port(starting_port=8000, max_attempts=100):
    port = starting_port
    for _ in range(max_attempts):
        if not __is_port_in_use(port):
            return port
        port += 1
    raise RuntimeError("No available ports found")


def _wait_for_server_to_start(timeout=SERVER_START_TIMEOUT):
    log_file_path = "process.log"
    start_time = time.time()
    last_position = 0

    while time.time() - start_time < timeout:
        with open(log_file_path, "r") as log_file:
            # Move to the last read position
            log_file.seek(last_position)
            # Read new lines
            new_lines = log_file.readlines()
            # Update the last read position
            last_position = log_file.tell()

            for line in new_lines:
                print(line.strip())  # Print each new line
                if "Uvicorn running on" in line:
                    logger.info("Server started successfully")
                    return True
                if "Traceback" in line:
                    logger.error("Error detected in log: {}", line.strip())
                    # Print the entire traceback
                    traceback_lines = [line.strip()]
                    for tb_line in new_lines[new_lines.index(line) + 1:]:
                        traceback_lines.append(tb_line.strip())
                        if tb_line.strip() == "":
                            break
                    for tb_line in traceback_lines:
                        logger.error(tb_line)
                    return False

        time.sleep(1)

    logger.error("Server did not start within the timeout period")
    return False


def _start_server():
    if __check_service_health():
        logger.info("Service is already running")
        return
    else:
        logger.info("Starting service...")
        logger.info("Starting the service for the first time may take some time, please be patient.")
        port = read_port()
        if not port:
            port = 8000  # Default port
            __create_port(port)

        if __is_port_in_use(port):
            logger.warning(f"Port {port} is already in use. Finding a new port...")
            port = __find_available_port(port)
            update_port(port)
        log_file_path = "process.log"

        # 打开日志文件
        with open(log_file_path, "w") as log_file:
            # 启动子进程，并将标准输出和标准错误输出重定向到日志文件
            subprocess.Popen(
                ["ai_server","-r", f"--port={port}"],
                stdout=log_file,
                stderr=log_file
            )

        logger.info("Server is starting on port {}...", port)

        # Wait for the server to start
        if not _wait_for_server_to_start():
            raise RuntimeError("The server did not start within the timeout period, please check the error messages.")
        return
