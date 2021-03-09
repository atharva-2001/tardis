from tardis.util.colored_logger import ColoredFormatter, formatter_message
from loguru import logger
from functools import partialmethod
import logging
import sys
import contextlib
import warnings
import astropy
import pyne


def verbosity_filter(record):
    if record["extra"].get("warn_and_above"):
        return record["level"].no >= logger.level("WARNING").no

    if record["extra"].get("info_and_above"):
        return record["level"].no >= logger.level("INFO").no

    if record["extra"].get("tardis_info_and_above"):
        # logger.disable("astropy")
        return record["level"].no >= logger.level("TARDIS INFO").no

    return True


logger = logger.patch(lambda record: record.update(name="astropy"))
logger = logger.patch(lambda record: record.update(name="sys"))
logger = logger.patch(lambda record: record.update(name="tardis"))
logger = logger.patch(lambda record: record.update(name="py.warnings"))


logger = logger.patch(
    lambda record: record["extra"].update(name="_astropy_init")
)

logger.__class__.special_info = partialmethod(
    logger.__class__.log, "special_info", no=35
)

logger.add(sys.stderr, level="DEBUG", filter=verbosity_filter)
logger.remove()


def showwarning(message, *args, **kwargs):
    logger.warning(message)
    # showwarning_(message, *args, **kwargs)


warnings.showwarning = showwarning


# format_ = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <bold><level>{level: <8}</level></bold> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
format_ = "  [ <bold><level>{level: <8}</level></bold> ][ <blue>{name}</blue>:<blue>{function}</blue>:<blue>{line}</blue>]- <cyan>{message}</cyan>"

logger.level("TARDIS INFO", no=35, color="<magenta>")
logger.__class__.tardis_info = partialmethod(
    logger.__class__.log,
    "TARDIS INFO",
)

logger.add(
    sys.stdout,
    filter=verbosity_filter,
    level="TRACE",
    catch=True,
    format=format_,
    colorize=True,
    backtrace=True,
)
