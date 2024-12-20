import argparse
from loguru import logger

import psutil
import os
import json
import sys


def get_cache_dir():
    home_dir = os.path.expanduser('~')
    # Join .cache directory
    cache_dir = os.path.join(home_dir, '.cache')
    return cache_dir


def load_config(config_file='model_lib/config.json'):
    path = os.path.join(get_cache_dir(), config_file)
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


import requests


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


def find_and_kill_process(port):
    """Find and terminate the process occupying the specified port."""
    try:
        # Check if the platform supports 'connections' attribute
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            try:
                # Try to get the connections attribute (this may fail on certain platforms)
                connections = proc.connections(kind='inet')
                for conn in connections:
                    if conn.laddr.port == port:
                        logger.debug(
                            f"Found process {proc.info['name']} (PID: {proc.info['pid']}) occupying port {port}")
                        proc.terminate()  # Terminate the process
                        logger.debug(f"Terminated process {proc.info['pid']}.")
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
                pass  # Handle platforms where connections are not available
    except Exception as e:
        logger.error(f"Error: {e}")

    logger.debug(f"No process found occupying port {port}.")


def check_libraries():
    try:
        import transformers
        logger.debug("transformers is installed.")
    except ImportError:
        logger.error("transformers is not installed. Please install it using: pip install paddlepaddle")
        sys.exit()
    try:
        import paddle
        logger.debug("paddlepaddle is installed.")
    except ImportError:
        logger.error("paddlepaddle is not installed. Please install it using: pip install paddlepaddle")
        sys.exit()


def main():
    parser = argparse.ArgumentParser(description="Manage FastAPI OCR server.")
    parser.add_argument("-r", "--run", action="store_true", help="Run the FastAPI server")
    parser.add_argument("-t", "--test", action="store_true", help="Test if the server is running")
    parser.add_argument("-c", "--close", action="store_true",
                        help="Close the process running on the port specified in config.json")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--lang", type=str, default='en', help="Language for OCR")
    args = parser.parse_args()

    if args.run:
        check_libraries()
        import json
        import os
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
        from typing import List
        from paddleocr import PaddleOCR
        from PIL import Image
        from tensorflow.keras.preprocessing import image
        from tensorflow.keras.models import load_model
        from cathin.model_service.class_type import var

        # Initialize PaddleOCR with default language as 'en'
        ocr = None

        florence_2_base_weights_path, florence_2_base_processor_path, ico_recognition_model_path = check_and_download_models()

        # Check if GPU is available
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        processor = AutoProcessor.from_pretrained(florence_2_base_processor_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(florence_2_base_weights_path,
                                                     torch_dtype=torch.float16 if device == 'cuda' else torch.float32,
                                                     trust_remote_code=True).to(device)

        ico_recognition_model_path = ico_recognition_model_path + '/ico_recognition_model.h5'
        class_detection_model = load_model(ico_recognition_model_path)

        CONFIG_FILE = 'model_lib/config.json'

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

        def generate_captions_from_images(cropped_images, prompt=None):
            """
            Generate image descriptions.

            :param cropped_images: List[PIL.Image.Image] - List of cropped images.
            :param caption_model_processor: dict - Model and processor.
            :param prompt: str - Prompt.
            :return: List[str] - List of descriptions.
            """
            prompt = prompt or "The image shows"
            generated_texts = []
            device = model.device

            # Process images in batches, with a maximum of 10 images per batch
            batch_size = 10
            for i in range(0, len(cropped_images), batch_size):
                batch_images = cropped_images[i:i + batch_size]
                inputs = processor(images=batch_images, text=[prompt] * len(batch_images), return_tensors="pt",
                                   padding=True).to(device)

                # Convert pixel values to float16
                # inputs['pixel_values'] = inputs['pixel_values'].half()

                generated_ids = model.generate(**inputs, max_length=100, num_beams=5, no_repeat_ngram_size=2,
                                               early_stopping=True)
                generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)
                generated_texts.extend([text.strip() for text in generated_text])
            return generated_texts

        app = FastAPI()

        class PredictionRequest(BaseModel):
            input_text: str
            num_return_sequences: int = 1
            num_beams: int = 1
            do_sample: bool = False

        class ImageRequest(BaseModel):
            images: List[str]
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
                for img_str in images_base64:
                    img_data = base64.b64decode(img_str)
                    img = Image.open(BytesIO(img_data)).convert("RGB")  # Decode from base64 and convert to RGB
                    cropped_images.append(img)

                prompt = request.prompt
                descriptions = generate_captions_from_images(cropped_images, prompt)
                return JSONResponse(content={'descriptions': descriptions}, status_code=200)

            except Exception as e:
                logger.error(f"Error processing request: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to process images: {str(e)}")

        # Run the server
        save_config(args.port, args.lang)
        ocr = PaddleOCR(use_angle_cls=True, lang=args.lang)
        uvicorn.run(app, host="0.0.0.0", port=args.port)

    elif args.test:
        logger.debug("Testing service status...")
        # Test if the server is running
        config = load_config()
        service_url = f"http://localhost:{config['port']}/health"
        check_service_status(service_url)


    elif args.close:
        # Close the process running on the port specified in the config.json
        config = load_config()
        find_and_kill_process(config['port'])
