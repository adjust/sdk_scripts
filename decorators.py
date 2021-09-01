import platform


def only_mac_os(func):
    """Decorator for macOS only functions."""
    def wrapper(*args, **kwargs):
        if platform.system() == 'Darwin':
            func(*args, **kwargs)
        else:
            print(f'[{func.__name__}] This is not working on {platform.system()} only for Mac!')

    return wrapper
