import subprocess

def get_android_devices():
    """Get connected Android devices via adb"""
    try:
        adb_output = subprocess.check_output(["adb", "devices"]).decode("utf-8")
        devices = [line.split()[0] for line in adb_output.splitlines()[1:] if line.strip()]
        return devices
    except subprocess.CalledProcessError:
        return ["No devices found"]

def get_ios_devices():
    """Get connected iOS devices via idevice_id"""
    try:
        idevice_output = subprocess.check_output(["tidevice", "list"]).decode("utf-8")
        devices = idevice_output.splitlines()
        return devices
    except subprocess.CalledProcessError:
        return ["No devices found"]