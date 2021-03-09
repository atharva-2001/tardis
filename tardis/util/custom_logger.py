from tardis.util.colored_logger import ColoredFormatter, formatter_message
from loguru import logger
from functools import partialmethod
import logging
import sys
import contextlib
import warnings
import astropy

# FORMAT = "[$BOLD%(name)-20s$RESET][%(levelname)-18s]  %(message)s ($BOLD%(filename)s$RESET:%(lineno)d)"
# COLOR_FORMAT = formatter_message(FORMAT, True)
# COLORED_FORMAT = ColoredFormatter(COLOR_FORMAT)
# formatted_string = vars(COLORED_FORMAT)["_fmt"]
# class StreamToLogger:
#     def __init__(self, level="INFO"):
#         self._level = level

#     def write(self, buffer):
#         for line in buffer.rstrip().splitlines():
#             logger.opt(depth=1).log(self._level, line.rstrip())

#     def flush(self):
#         pass


# logger.remove()
# logger.add(sys.__stdout__)

# stream = StreamToLogger()
# with contextlib.redirect_stdout(stream):
#     print("Standard output is sent to added handlers.")

# showwarning_ = warnings.showwarning


# def showwarning(message, *args, **kwargs):
#     logger.warning(message)
#     showwarning_(message, *args, **kwargs)


# warnings.showwarning = showwarning


# logger = logger.patch(lambda record: record["extra"].update(name="astropy"))
# logger = logger.patch(lambda record: record["extra"].update(name="sys"))
# logger = logger.patch(
#     lambda record: record["extra"].update(name="_astropy_init")
# )

# logger.__class__.special_info = partialmethod(
#     logger.__class__.log, "special_info", no=35
# )

# logger.add(sys.stderr, level="DEBUG")
# logger.remove()


def verbosity_filter(record):
    if record["extra"].get("warn_and_above"):
        return record["level"].no >= logger.level("WARNING").no

    if record["extra"].get("info_and_above"):
        return record["level"].no >= logger.level("INFO").no

    if record["extra"].get("tardis_info_and_above"):
        # logger.disable("astropy")
        return record["level"].no >= logger.level("TARDIS INFO").no

    return True


# format_ = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <bold><level>{level: <8}</level></bold> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# logger.level("TARDIS INFO", no=35, color="<blue><bold>")
# logger.__class__.tardis_info = partialmethod(
#     logger.__class__.log,
#     "TARDIS INFO",
# )

# logger.add(
#     sys.stderr,
#     filter=verbosity_filter,
#     level="DEBUG",
#     catch=True,
#     format=format_,
#     colorize=True,
# )
