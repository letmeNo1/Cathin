import tkinter as tk
from tkinter import ttk
from cathin.console_scripts.cat_ui.get_devices import get_android_devices, get_ios_devices
from cathin.console_scripts.cat_ui.screenshot import open_screenshot_window

def create_platform_selection_window(root):
    # Get the screen width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Set the window width and height
    window_width = 500
    window_height = 300

    # Calculate the position of the window to ensure it is centered on the screen
    x_position = (screen_width // 2) - (window_width // 2)
    y_position = (screen_height // 2) - (window_height // 2)

    # Set the position of the window
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # Create a Frame for horizontally arranging the label and combobox
    platform_frame = tk.Frame(root)
    platform_frame.pack(pady=10)

    # Create platform selection box (label + combobox)
    platform_label = tk.Label(platform_frame, text="Select Platform:")
    platform_label.pack(side="left", padx=5)  # Label and combobox displayed side by side

    platform_var = tk.StringVar()
    platform_var.set("Android")  # Default selection is Android

    # Create combobox using ttk.Combobox
    platform_combobox = ttk.Combobox(platform_frame, textvariable=platform_var, values=["Android", "iOS", "PC"])
    platform_combobox.pack(side="left", padx=5)  # Combobox and label displayed side by side

    # Create device selection box (for Android and iOS)
    device_frame = tk.Frame(root)  # Create a new Frame for device selection
    device_frame.pack(pady=5)

    # Create device selection box label (displayed in parallel)
    device_label = tk.Label(device_frame, text="Select Device:")
    device_label.pack(side="left", padx=5)

    # Create device selection box, initially disabled
    device_combobox = ttk.Combobox(device_frame, state="disabled")  # Initially disabled
    device_combobox.pack(side="left", padx=5)

    # Create window name entry box (for PC only)
    window_name_label = tk.Label(root, text="Enter Window Name (for PC only):")
    window_name_entry = tk.Entry(root)

    # Initially hide the window name entry box
    window_name_label.pack_forget()
    window_name_entry.pack_forget()

    # Listen for changes in platform selection
    platform_combobox.bind("<<ComboboxSelected>>", lambda event: update_ui_for_platform(
        platform_var.get(), device_combobox, window_name_label, window_name_entry, device_frame))

    # Create language selection box (label + combobox)
    language_frame = tk.Frame(root)
    language_frame.pack(pady=10)

    language_label = tk.Label(language_frame, text="Select Language:")
    language_label.pack(side="left", padx=5)

    language_var = tk.StringVar()
    language_var.set("en")  # Default selection is English

    # Create combobox using ttk.Combobox
    language_combobox = ttk.Combobox(language_frame, textvariable=language_var, values=["en", "ch"])
    language_combobox.pack(side="left", padx=5)  # Combobox and label displayed side by side

    # Create start button (always at the bottom of the window)
    start_button = tk.Button(root, text="Start", command=lambda: on_start_button_click(
        platform_var.get(), device_combobox.get(), window_name_entry.get(), language_var.get()))
    start_button.pack(side="bottom", pady=10)

def update_ui_for_platform(platform, device_combobox, window_name_label, window_name_entry, device_frame):
    """Update UI content based on the selected platform"""
    if platform == "Android" or platform == "iOS":
        # Show device selection box and disable window name entry box
        devices = get_android_devices() if platform == "Android" else get_ios_devices()
        device_combobox["values"] = devices
        device_combobox.state(["!disabled"])  # Enable device selection box

        # Hide window name entry box
        window_name_label.pack_forget()
        window_name_entry.pack_forget()

        # Ensure device selection box is displayed
        device_frame.pack(pady=5)

    elif platform == "PC":
        # Hide and disable device selection box
        device_combobox["values"] = []
        device_combobox.state(["disabled"])

        # Show window name entry box
        window_name_label.pack(pady=5)
        window_name_entry.pack(pady=5)

        # Hide device selection box
        device_frame.pack_forget()

def on_start_button_click(platform, device_udid, window_name, language):
    # Check the platform and pass the relevant parameters to open_screenshot_window
    if platform == "Android" or platform == "iOS":
        if not device_udid:
            print("Device UDID is required!")
            return
        open_screenshot_window(platform, device_udid=device_udid, language=language)
    elif platform == "PC":
        if not window_name:
            print("Window name is required for PC!")
            return
        open_screenshot_window(platform, window_name=window_name, language=language)

# Main program start
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Platform Selection")
    create_platform_selection_window(root)
    root.mainloop()