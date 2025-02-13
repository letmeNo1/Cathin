import os
import json

CONFIG_FILE = 'model_lib/config.json'


def get_cache_dir():
    home_dir = os.path.expanduser('~')
    # Join the .cache directory
    cache_dir = os.path.join(home_dir, '.cache')
    return cache_dir


def get_config_file_path():
    cache_dir = get_cache_dir()
    config_file_path = os.path.join(cache_dir, CONFIG_FILE)
    return config_file_path


def create_config_file_if_not_exists():
    config_file_path = get_config_file_path()
    # Get directory path
    config_dir = os.path.dirname(config_file_path)

    # If the directory does not exist, create it
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    # If the file does not exist, create it and write default content
    if not os.path.exists(config_file_path):
        with open(config_file_path, 'w') as config_file:
            json.dump({"port": 8080}, config_file, indent=4)


def read_port():
    config_file_path = get_config_file_path()
    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as file:
            config = json.load(file)
            return config.get('port')
    else:
        # If the file does not exist, create it and write default content
        create_config_file_if_not_exists()
        return 8080


def update_port(new_port):
    config_file_path = get_config_file_path()
    config = {}
    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as file:
            config = json.load(file)
    config['port'] = new_port
    with open(config_file_path, 'w') as file:
        json.dump(config, file, indent=4)


def create_port(new_port):
    config_file_path = get_config_file_path()
    config = {'port': new_port}
    with open(config_file_path, 'w') as file:
        json.dump(config, file, indent=4)
