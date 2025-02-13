from loguru import logger


class MultipleValuesFoundError(Exception):
    """Custom exception class for throwing an exception when multiple identical values are found"""

    def __init__(self, message, keys_values):
        super().__init__(message)
        self.keys_values = keys_values

    def __str__(self):
        keys_values_str = "\n".join([str(item) for item in self.keys_values])
        return f"{self.args[0]}:\n{keys_values_str}"


class TimeoutNotFoundError(Exception):
    """Custom exception class for throwing an exception when a matching value is not found within a timeout"""

    def __init__(self, message):
        super().__init__(message)


def search_data(data, **query):
    logger.debug(f"Searching for query: {query}")
    if 'text_contains' in query:
        method = 'text_contains'
        search_value = query['text_contains']
    elif 'id_contains' in query:
        method = 'id_contains'
        search_value = query['id_contains']
    elif 'text' in query:
        method = 'text'
        search_value = query['text']
    elif 'id' in query:
        method = 'id'
        search_value = query['id']
    elif 'index' in query:
        method = 'index'
        search_value = query['index']
    else:
        raise ValueError("One of 'id', 'text', 'index', 'text_contains', or 'id_contains' must be provided")

    found_keys_values = []

    for index, item in enumerate(data):
        for key, value in item.items():
            if method == 'text' and isinstance(value, str) and value.strip() == search_value:
                found_keys_values.append([index, key, value])
            elif method == 'text_contains' and isinstance(value, str) and search_value in value:
                found_keys_values.append([index, key, value])
            elif method == 'id' and isinstance(value, list) and value[0] == 'icon' and value[1] == search_value:
                found_keys_values.append([index, key, value])
            elif method == 'id_contains' and isinstance(value, list) and value[0] == 'icon' and search_value in value[1]:
                found_keys_values.append([index, key, value])

    if method == 'index':
        if 0 <= search_value < len(data):
            return [data[search_value]]

    if len(found_keys_values) == 0:
        raise TimeoutNotFoundError(f"Query '{search_value}' not found in current page")
    return found_keys_values


def find_by_method(data, **query):
    return search_data(data, **query)
