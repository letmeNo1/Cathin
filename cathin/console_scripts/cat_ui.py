import subprocess

import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk

from cathin.common.get_all_bounds_and_labels import get_all_bounds_and_labels
from cathin.common.request_api import _call_generate_image_caption_api,\
    _start_server
from cathin.common.utils import _crop_and_encode_image


class ImageProcessor:
    def __init__(self, img, bounds):
        self.img = img
        self.bounds = bounds

    @property
    def icon_description(self):
        a = _crop_and_encode_image(self.img, [self.bounds])
        text = _call_generate_image_caption_api(a)
        return text


# Image processing function
def process_and_get_image(udid):
    """Get image from device, process and draw annotations, return processed image and text information"""
    try:
        # image_path = r"C:\Users\hanhuang\Documents\apollo-tools\ApolloModule\ApolloCathin\cathin\console_scripts\original.jpg"  # 替换为本地图像的路径
        #
        # # 使用 OpenCV 读取本地图像
        # img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        result = subprocess.run(['adb', '-s', udid, 'exec-out', 'screencap', '-p'], stdout=subprocess.PIPE)
        screenshot_data = result.stdout
        nparr = np.frombuffer(screenshot_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        all_bounds = get_all_bounds_and_labels(img, True)
        # Draw boxes and annotations
        for index, box_dict in enumerate(all_bounds):
            box = list(box_dict.keys())[0]
            text = box_dict[box]
            # des = f"{index} {text}" if text else str(index)
            des = f"{index}"
            x, y, w, h = box
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), 2)
            cv2.putText(img, des, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
            cv2.putText(img, des, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 1)

        return img, all_bounds
    except Exception as e:
        print(f"Error processing image: {e}")
        return None, None


# Tkinter display function
def load_and_show_image(udid):
    """Load processed image and display it on the interface"""
    # Call processing function to get processed image and text information
    img, all_text_bounds_and_des = process_and_get_image(udid)

    if img is None:
        return

    # Convert OpenCV image to PIL image
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    # Get original dimensions
    original_width, original_height = img_pil.size

    # Scale image to 1/5 of its width and height
    if original_width < original_height:
        if original_width > 400:
            scale_factor = 400 / original_width
            new_width = 400
            new_height = int(original_height * scale_factor)
    else:
        if original_width > 900:
            scale_factor = 900 / original_width
            new_width = 900
            new_height = int(original_height * scale_factor)
    img_pil = img_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
    print(new_width,new_height)

    # Convert image to a format usable by Tkinter
    img_tk = ImageTk.PhotoImage(img_pil)

    # Display image in Tkinter label
    label.config(image=img_tk)
    label.image = img_tk  # Prevent image from being garbage collected

    # Display OCR results in the right-side Canvas
    for widget in listbox_frame.winfo_children():
        widget.destroy()

    for index,item in enumerate(all_text_bounds_and_des):
        print(item.items())
        for key, value in item.items():
            frame = tk.Frame(listbox_frame)
            print(value)

            if isinstance(value, list):
                value = value[1]
                label_text = tk.Label(frame, text=f"{index}.{key}: id= {value}")
            else:
                label_text = tk.Label(frame, text=f"{index}.{key}: text= {value}")

            if isinstance(value, list):
                processor = ImageProcessor(img, key)
                button = tk.Button(frame, text="Button", command=lambda p=processor, l=label_text: update_text(p, l))
                button.pack(side=tk.LEFT)
            label_text.pack(side=tk.LEFT)
            frame.pack(fill=tk.X)

    # Dynamically adjust window size
    app.geometry(f"{new_width * 3}x{new_height}")  # Set window width to three times the image width


def update_text(processor, label):
    """Update text"""
    new_text = processor.icon_description
    label.config(text=new_text)


app = tk.Tk()
app.title("Processed Image Viewer")

# Create main frame, dividing the window into left and right parts
main_frame = tk.Frame(app)
main_frame.grid(row=0, column=0, sticky="nsew")

# Set row and column weights for `main_frame` to fill the window
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, weight=1)

# Left frame: for displaying the image
left_frame = tk.Frame(main_frame)
left_frame.grid(row=0, column=0, sticky="nsew")

label = tk.Label(left_frame)  # For displaying the image
label.grid(row=0, column=0, sticky="nsew")

# Right frame: for displaying text information
right_frame = tk.Frame(main_frame)
right_frame.grid(row=0, column=1, sticky="nsew")

# Set row and column weights for `right_frame` to fill the frame
right_frame.grid_rowconfigure(0, weight=1)
right_frame.grid_columnconfigure(0, weight=1)

# Create Canvas and scrollbar
canvas = tk.Canvas(right_frame)
scrollbar = tk.Scrollbar(right_frame, orient=tk.VERTICAL, command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create a Frame inside the Canvas
listbox_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=listbox_frame, anchor="nw")

# Configure Canvas scroll region
listbox_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# Adjust left and right proportions to each take half
main_frame.grid_columnconfigure(0, weight=1)  # Left frame takes 50%
main_frame.grid_columnconfigure(1, weight=1)  # Right frame takes 50%


def main():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', type=str, help='device_udid')
    args = parser.parse_args()

    _start_server()
    # Load and display image on program start
    # load_and_show_image(args.s)
    load_and_show_image(args.s)
    # Start Tkinter application
    app.mainloop()

main()