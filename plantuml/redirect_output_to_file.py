import contextlib

def redirect_output_to_file(file_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with open(file_name, 'w') as f:
                with contextlib.redirect_stdout(f):
                    return func(*args, **kwargs)
        return wrapper
    return decorator