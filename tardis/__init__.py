# Licensed under a 3-clause BSD style license - see LICENSE.rst
import sys
import logging
import warnings
from loguru import logger
import contextlib
import astropy
from functools import partialmethod
import pyne.data

from tardis.util.colored_logger import ColoredFormatter, formatter_message

# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *

# ----------------------------------------------------------------------------

from tardis.base import run_tardis
from tardis.io.util import yaml_load_config_file as yaml_load
from tardis.util.custom_logger import logger, verbosity_filter

warnings.filterwarnings("ignore", category=pyne.utils.QAWarning)


class StreamToLogger:
    def __init__(self, level="INFO"):
        self._level = level

    def write(self, buffer):
        for line in buffer.rstrip().splitlines():
            logger.opt(depth=1).log(self._level, line.rstrip())

    def flush(self):
        pass


logger.remove()
logger.add(sys.__stdout__)

stream = StreamToLogger()
with contextlib.redirect_stdout(stream):
    print("Standard output is sent to added handlers.")


showwarning_ = warnings.showwarning


def showwarning(message, *args, **kwargs):
    logger.warning(message)
    showwarning_(message, *args, **kwargs)


warnings.showwarning = showwarning

logger = logger.patch(lambda record: record["extra"].update(name="astropy"))
logger = logger.patch(lambda record: record["extra"].update(name="sys"))
logger = logger.patch(lambda record: record["extra"].update(name="tardis"))

logger = logger.patch(
    lambda record: record["extra"].update(name="_astropy_init")
)

logger.__class__.special_info = partialmethod(
    logger.__class__.log, "special_info", no=35
)

logger.add(sys.stderr, level="DEBUG")
logger.remove()


format_ = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <bold><level>{level: <8}</level></bold> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

logger.level("TARDIS INFO", no=35, color="<blue><bold>")
logger.__class__.tardis_info = partialmethod(
    logger.__class__.log,
    "TARDIS INFO",
)

logger.add(
    sys.stderr,
    filter=verbosity_filter,
    level="DEBUG",
    catch=True,
    format=format_,
    colorize=True,
)
# FORMAT = "[$BOLD%(name)-20s$RESET][%(levelname)-18s]  %(message)s ($BOLD%(filename)s$RESET:%(lineno)d)"
# COLOR_FORMAT = formatter_message(FORMAT, True)

# logging.captureWarnings(True)
# logger = logging.getLogger("tardis")
# logger.setLevel(logging.INFO)

# console_handler = logging.StreamHandler(sys.stdout)
# console_formatter = ColoredFormatter(COLOR_FORMAT)
# console_handler.setFormatter(console_formatter)

# logger.addHandler(console_handler)
# logging.getLogger("py.warnings").addHandler(console_handler)
