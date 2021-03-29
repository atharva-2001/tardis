import logging
import numpy as np
import os
from functools import wraps

DEBUG_MODE = True
LOG_FILE = "test_log2.log"
BUFFER = 1
ticker = 1

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.handlers = []

if LOG_FILE:
    file_ = open(LOG_FILE, "a")
    logger.propagate = False
    console_handler = logging.FileHandler(LOG_FILE)
else:
    console_handler = logging.StreamHandler()

console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def log_data(data): 
    if int(os.path.getsize(LOG_FILE))> 10000000:
        pass
    else:
        if  type(data) is np.ndarray:
            file_.write(str(list(data)))
        else: 
            file_.write(data)
    

def log_decorator(func):
    """
    Decorator to log functions while in debug mode, i.e., when
    `debug_montecarlo` is True in the config. Works for
    `@jit'd and `@njit`'d functions, but with a significant speed
    penalty.

    TODO: in nopython mode: do I need a context manager?

    Input:
        func : (function) function to be logged.

    Output:
        wrapper : (function) wrapper to the function being logged.
    """

    # to ensure that calling `help` on the decorated function still works
    # @wraps(func)
    def wrapper(*args, **kwargs):
        """
        Wrapper to the log_decorator.

        When called, it has the side effect of
        logging every `BUFFER` input and output to `func`, if `DEBUG_MODE` is
        `True`.

        Input:
            *args : arguments to be passed to `func`.
            **kwargs : keyword arguments to be passed to `func`.

        Output:
            result : result of calling `func` on `*args` and `**kwargs`.
        """
        result = func(*args, **kwargs)
        if DEBUG_MODE:
            global ticker
            ticker += 1
            if ticker % BUFFER == 0:  # without a buffer, performance suffers
                logger.debug(f"Func: {func.__name__}. Input: {(args, kwargs)}")
                logger.debug(f"Output: {result}.")
        return result

    return wrapper
