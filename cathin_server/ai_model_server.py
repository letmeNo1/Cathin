import argparse
import zipfile

from loguru import logger

import os
import json
import sys
import requests

var = {
    0: "add",
    1: "arrow_backward",
    2: "arrow_downward",
    3: "arrow_forward",
    4: "arrow_upward",
    5: "attach_file",
    6: "av_forward",
    7: "av_rewind",
    8: "avatar",
    9: "bluetooth",
    10: "book",
    11: "bookmark",
    12: "build",
    13: "call",
    14: "cart",
    15: "chat",
    16: "check",
    17: "close",
    18: "compare",
    19: "copy",
    20: "dashboard",
    21: "date_range",
    22: "delete",
    23: "description",
    24: "dialpad",
    25: "edit",
    26: "email",
    27: "emoji",
    28: "expand_less",
    29: "expand_more",
    30: "explore",
    31: "facebook",
    32: "favorite",
    33: "file_download",
    34: "filter",
    35: "filter_list",
    36: "flag",
    37: "flash",
    38: "flight",
    39: "folder",
    40: "follow",
    41: "font",
    42: "fullscreen",
    43: "gift",
    44: "globe",
    45: "group",
    46: "help",
    47: "history",
    48: "home",
    49: "info",
    50: "label",
    51: "launch",
    52: "layers",
    53: "list",
    54: "location",
    55: "location_crosshair",
    56: "lock",
    57: "menu",
    58: "microphone",
    59: "minus",
    60: "more",
    61: "music",
    62: "national_flag",
    63: "navigation",
    64: "network_wifi",
    65: "notifications",
    66: "pause",
    67: "photo",
    68: "play",
    69: "playlist",
    70: "power",
    71: "refresh",
    72: "repeat",
    73: "save",
    74: "search",
    75: "send",
    76: "settings",
    77: "share",
    78: "shop",
    79: "skip_next",
    80: "skip_previous",
    81: "sliders",
    82: "star",
    83: "stop",
    84: "swap",
    85: "switcher",
    86: "thumbs_down",
    87: "thumbs_up",
    88: "time",
    89: "twitter",
    90: "undo",
    91: "videocam",
    92: "visibility",
    93: "volume",
    94: "wallpaper",
    95: "warning",
    96: "weather",
    97: "zoom_out"
}


def get_current_path():
    current_file_path = os.path.abspath(__file__)
    # Get the current script directory
    current_dir = os.path.dirname(current_file_path).replace("console_scripts", "")
    return current_dir


def load_config(config_file='config.json'):
    path = os.path.join(get_current_path(), config_file)
    try:
        with open(path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file {config_file} not found!")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Configuration file {config_file} has an invalid format!")
        sys.exit(1)


def check_service_status(url):
    """Check if the service is running properly"""
    try:
        # Send a GET request to the service
        response = requests.get(url)
        # Check if the status code is 200 (i.e., the service is running)
        if response.status_code == 200:
            logger.debug(f"The service at {url} is running normally!")
        else:
            logger.error(f"The service returned an unexpected status code {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        # Handle connection errors or request exceptions
        logger.error(f"Unable to connect to the service: {e}")




def extract(extract_to):
    model_dir = os.path.join(get_current_path(), 'model', 'huggingface.zip')
    # Unzip the file
    with zipfile.ZipFile(model_dir, 'r') as zip_ref:
        zip_ref.extractall(extract_to)


def check_florence_model():
    home_dir = os.path.expanduser("~")
    cache_dir = os.path.join(home_dir, ".cache")
    huggingface_dir = os.path.join(cache_dir, "huggingface")

    if not os.path.exists(huggingface_dir):
        extract(cache_dir)



def main():
    parser = argparse.ArgumentParser(description="Manage FastAPI OCR server.")
    parser.add_argument("-r", "--run", action="store_true", help="Run the FastAPI server")
    parser.add_argument("-t", "--test", action="store_true", help="Test if the server is running")
    parser.add_argument("-c", "--close", action="store_true",
                        help="Close the process running on the port specified in config.json")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--lang", type=str, default='en', help="Language for OCR")
    args = parser.parse_args()
    check_florence_model()

    if args.run:
        model_dir = os.path.join(get_current_path(), 'model')
        florence_2_weights = os.path.join(model_dir, "florence_2_weights")
        import json
        import traceback
        import numpy as np
        import uvicorn
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel
        import torch
        from transformers import AutoProcessor, AutoModelForCausalLM
        import base64
        from io import BytesIO
        from paddleocr import PaddleOCR
        from PIL import Image
        from tensorflow.keras.preprocessing import image
        from tensorflow.keras.models import load_model
        # Initialize PaddleOCR with default language as 'en'
        ocr = None

        # Check if GPU is available
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        processor = AutoProcessor.from_pretrained(os.path.join(model_dir, "florence_2_processor"),
                                                  trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(florence_2_weights,
                                                     torch_dtype=torch.float16 if device == 'cuda' else torch.float32,
                                                     trust_remote_code=True).to(device)

        ico_recognition_model_path = os.path.join(model_dir, 'ico_recognition_model', 'ico_recognition_model.h5')
        class_detection_model = load_model(ico_recognition_model_path)

        CONFIG_FILE = os.path.join(model_dir, 'config.json')

        def save_config(port, lang):
            config_data = {
                "port": port,
                "lang": lang
            }

            # Create directory if it does not exist
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

            # Write configuration data to JSON file
            with open(CONFIG_FILE, 'w') as config_file:
                json.dump(config_data, config_file, indent=4)

        def preprocess_image(img):
            img = img.convert("RGB")  # Convert image to RGB format
            img = img.resize((32, 32))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array /= 255.0  # Normalize the image array
            return img_array

        def classify_image(img):
            img_array = preprocess_image(img)
            predictions = class_detection_model.predict(img_array)[0]

            # Get the top three predictions and their corresponding classes
            top_indices = np.argsort(predictions)[-3:][::-1]
            top_scores = predictions[top_indices]

            top_classes = [(var[idx], float(score)) for idx, score in zip(top_indices, top_scores)]

            return top_classes

        def generate_captions_from_images(cropped_images, prompt="<CAPTION>"):
            """
            Generate image descriptions.

            :param cropped_images: List[PIL.Image.Image] - List of cropped images.
            :param caption_model_processor: dict - Model and processor.
            :param prompt: str - Prompt.
            :return: List[str] - List of descriptions.
            """
            prompt = "The image show"

            # Preprocess the image and generate the caption
            inputs = processor(images=cropped_images, text=prompt, return_tensors="pt").to(
                "cuda" if torch.cuda.is_available() else "cpu")
            outputs = model.generate(**inputs)

            # Decode the caption
            description = processor.decode(outputs[0], skip_special_tokens=True)
            return description

        app = FastAPI()

        class ImageRequest(BaseModel):
            images: str
            prompt: str = "The image shows"

        class ImageData(BaseModel):
            image_base64: str

        class OCRRequest(BaseModel):
            image: str
            lang: str = 'en'  # Default language is English

        @app.get("/health")
        def health_check():
            return {"message": "Service is running"}

        @app.post("/perform_ocr")
        def perform_ocr(request: OCRRequest):
            image_base64 = request.image
            all_text_bounds_and_des = []

            try:
                img_data = base64.b64decode(image_base64)
                img = Image.open(BytesIO(img_data)).convert("RGB")
                img = np.array(img)
                try:
                    ocr_result = ocr.ocr(img, cls=True)
                    logger.debug("OCR completed successfully")
                except Exception as e:
                    error_message = f"Error during OCR processing: {e}"
                    logger.error(error_message)
                    traceback.print_exc()
                    raise HTTPException(status_code=500, detail=error_message)

                for line in ocr_result:
                    for word_info in line:
                        text_bounds_and_des = {}
                        box = word_info[0]
                        text, confidence = word_info[1]
                        if confidence < 0.7:
                            continue
                        x1, y1 = map(int, box[0])
                        x2, y2 = map(int, box[2])
                        width = x2 - x1
                        height = y2 - y1
                        bounds = (x1, y1, width, height)
                        text_bounds_and_des[str(bounds)] = text  # Convert tuple to string
                        all_text_bounds_and_des.append(text_bounds_and_des)

                return JSONResponse(content={'ocr_result': all_text_bounds_and_des}, status_code=200)

            except Exception as e:
                error_message = f"Error processing OCR request: {e}"
                logger.error(error_message)
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"Failed to process image for OCR: {str(e)}")

        @app.post("/classify_image")
        async def classify_image_from_base64(image_data: ImageData):
            try:
                # Decode base64 image
                img_data = base64.b64decode(image_data.image_base64)
                img = Image.open(BytesIO(img_data))

                # Perform prediction
                top_classes = classify_image(img)

                return {"top_predictions": top_classes}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.post("/generate_image_caption")
        async def generate_image_caption(request: ImageRequest):
            """
            Receive base64 encoded images and return descriptions.
            """
            images_base64 = request.images
            cropped_images = []

            try:
                img_data = base64.b64decode(images_base64)
                img = Image.open(BytesIO(img_data)).convert("RGB")

                prompt = request.prompt
                descriptions = generate_captions_from_images(img, prompt)
                return JSONResponse(content={'descriptions': descriptions}, status_code=200)

            except Exception as e:
                logger.error(f"Error processing request: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to process images: {str(e)}")

        # Run the server
        save_config(args.port, args.lang)
        ocr = PaddleOCR(use_angle_cls=True, lang=args.lang)
        uvicorn.run(app, host="0.0.0.0", port=args.port)


main()
