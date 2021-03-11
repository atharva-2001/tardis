from loguru import logger
from functools import partialmethod
import traceback
import sys
import warnings

# import tardis.util.logger_config

level = ""
logger.remove()


class verbosity_filter:
    def __init__(self, level, logger):
        self.level = level
        self.logger = logger

    def __call__(self, record):
        levelno = self.logger.level(self.level).no
        return record["level"].no >= levelno


# format of the message
format_ = "  [ <bold><level>{level: <8}</level></bold> ][ <blue>{name}</blue>:<blue>{function}</blue>:<blue>{line}</blue>]- <cyan>{message}</cyan>"

#  adding custom TARDIS INFO Level, just above WARNING
logger.level("TARDIS INFO", no=35, color="<magenta>")
logger.__class__.tardis_info = partialmethod(
    logger.__class__.log,
    "TARDIS INFO",
)

logger = logger.patch(lambda record: record["extra"].update(name="astropy"))
logger = logger.patch(lambda record: record["extra"].update(name="sys"))
logger = logger.patch(lambda record: record["extra"].update(name="tardis"))
logger = logger.patch(
    lambda record: record["extra"].update(name="tardis.plasma")
)
logger = logger.patch(lambda record: record["extra"].update(name="py.warnings"))
logger = logger.patch(
    lambda record: record["extra"].update(name="_astropy_init")
)

# tardis.util.logger_config.init()
# level = tardis.util.logger_config.level
# filter_ = tardis.util.logger_config.verbosity_filter(level, logger)


def reset_logger():
    filter_ = verbosity_filter(level, logger)
    logger.add(
        sys.stdout,
        filter=filter_,
        level="TRACE",
        # catch=True,
        format=format_,
        colorize=True,
        # backtrace=True,
    )


showwarning_ = warnings.showwarning


# capturing application warnings
def showwarning(message, *args, **kwargs):
    logger.warning(message)


warnings.showwarning = showwarning


def init():
    global level
    global reset_logger
    global remove_default