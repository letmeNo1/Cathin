import subprocess

# Parse the output of adb devices
def parse_adb_devices(output):
    lines = output.strip().splitlines()  # Remove leading and trailing whitespace and split the output by lines
    devices = []
    for line in lines[1:]:  # Skip the first line, which is the header
        parts = line.split()  # Split each line by spaces
        if len(parts) > 1 and parts[1] == "device":  # Ensure it is a connected device
            devices.append(parts[0])  # Device ID
    return devices

# Button click event handler function
def on_button_click(os_name):
    if os_name == "Android":
        # Get devices connected via ADB
        try:
            adb_devices_output = subprocess.check_output(["adb", "devices"], stderr=subprocess.STDOUT, text=True)
            devices = parse_adb_devices(adb_devices_output)

            # Here you can return the device list for dropdown selection
            if devices:
                print("Android Devices:", devices)
            else:
                print("No Android devices connected.")
        except subprocess.CalledProcessError as e:
            print("Error running adb devices.")
            print(e.output)