import cv2
from PIL import Image, ImageGrab, ImageTk
import subprocess
import threading
import tkinter as tk
from tkinter import Scrollbar, Toplevel, ttk, Button, messagebox
from cathin.Android.android_driver import AndroidDriver
from cathin.common.get_all_bounds_and_labels import get_all_bounds_and_labels
from cathin.console_scripts.cat_ui.image_porcessor import ImageProcessor

loading_window_ref = None

def open_screenshot_window(platform, device_udid=None, window_name=None, language=None):
    show_loading()
    threading.Thread(target=take_screenshot_and_show, args=(platform, device_udid, window_name, language)).start()

def take_screenshot_and_show(platform, device_udid, window_name, language):
    try:
        img = take_screenshot(platform, device_udid, window_name, language)
        all_text_bounds_and_des = get_all_bounds_and_labels(img, get_icon_des=True)
        all_values = []
        for index, box_dict in enumerate(all_text_bounds_and_des):
            box = list(box_dict.keys())[0]
            des = f"{index}"
            x, y, w, h = box
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), 2)
            cv2.putText(img, des, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
            cv2.putText(img, des, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 1)

        for index, entry in enumerate(all_text_bounds_and_des):
            for key, value in entry.items():
                if isinstance(value, list):
                    all_values.append(f"{index}.id:{value[1]}")
                else:
                    all_values.append(f"{index}.text:{value}")

        screenshot = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        hide_loading()
        show_screenshot(screenshot, all_values, all_text_bounds_and_des, img)
    except Exception as e:
        hide_loading()
        print(f"Error: {e}")

def show_loading():
    global loading_window_ref
    loading_window = Toplevel()
    loading_window.title("Loading...")
    loading_window.geometry("300x150")
    progress_bar = ttk.Progressbar(loading_window, mode='indeterminate')
    progress_bar.pack(pady=30)
    progress_bar.start()
    loading_window_ref = loading_window

def hide_loading():
    global loading_window_ref
    if loading_window_ref:
        loading_window_ref.destroy()
        loading_window_ref = None

def show_screenshot(screenshot, text_list, all_text_bounds_and_des, img):
    screenshot_window = Toplevel()
    screen_height = screenshot_window.winfo_screenheight()
    img_width, img_height = screenshot.size
    window_height = int(screen_height * 0.6) if img_width > img_height else int(screen_height * 0.8)
    window_width = int(window_height * img_width / img_height) + 300
    screenshot_window.title("Screenshot")
    screenshot_window.geometry(f"{window_width}x{window_height}")
    screenshot_window.resizable(False, False)
    screenshot_resized = screenshot.resize((window_width - 300, window_height), Image.Resampling.LANCZOS)
    screenshot_image = ImageTk.PhotoImage(screenshot_resized)
    main_frame = tk.Frame(screenshot_window)
    main_frame.pack(fill=tk.BOTH, expand=True)
    image_canvas = tk.Canvas(main_frame, width=window_width - 300, height=window_height)
    image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    image_canvas.create_image(0, 0, anchor=tk.NW, image=screenshot_image)
    text_frame = tk.Frame(main_frame, width=300)
    text_frame.pack(side=tk.LEFT, fill=tk.BOTH)
    scrollbar = Scrollbar(text_frame, orient=tk.VERTICAL)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    content_frame = tk.Frame(text_frame)
    content_frame.pack(fill=tk.BOTH, expand=True)
    scroll_canvas = tk.Canvas(content_frame, yscrollcommand=scrollbar.set)
    scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=scroll_canvas.yview)
    list_frame = tk.Frame(scroll_canvas)
    scroll_canvas.create_window((0, 0), window=list_frame, anchor=tk.NW)

    def show_description(index):
        show_loading()
        try:
            bounds = list(all_text_bounds_and_des[index].keys())[0]
            processor = ImageProcessor(img, bounds)
            description = processor.icon_description
            messagebox.showinfo("description", description, parent=screenshot_window)
        finally:
            hide_loading()

    def show_description_thread(index):
        threading.Thread(target=show_description, args=(index,)).start()

    for index, text in enumerate(text_list):
        row_frame = tk.Frame(list_frame)
        row_frame.pack(fill=tk.X, pady=5)
        show_button = Button(row_frame, text="des", command=lambda idx=index: show_description_thread(idx))
        show_button.pack(side=tk.LEFT, padx=5)
        label = tk.Label(row_frame, text=text, anchor='w', justify='left', width=35)
        label.pack(side=tk.LEFT, padx=5)

    list_frame.update_idletasks()
    scroll_canvas.config(scrollregion=scroll_canvas.bbox("all"))
    image_canvas.image = screenshot_image

def take_screenshot(platform, device_udid, window_name, language):
    if platform == "Android":
        android_driver = AndroidDriver(device_udid)
        img = android_driver._capture_screenshot()
        return img
    elif platform == "iOS":
        idevice_command = ["idevicescreenshot", "-u", device_udid, "screenshot.png"]
        subprocess.run(idevice_command)
        return Image.open("screenshot.png")
    elif platform == "PC":
        screenshot = ImageGrab.grab()
        return screenshot