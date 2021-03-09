from loguru import logger
from functools import partialmethod
import traceback
import sys
import warnings


def verbosity_filter(record):
    # if severity value is higher and equal to warning
    if record["extra"].get("warn_and_above"):
        return record["level"].no >= logger.level("WARNING").no

    # if severity value is higher and equal to info
    if record["extra"].get("info_and_above"):
        return record["level"].no >= logger.level("INFO").no

    # if severity value is higher and equal to tardis info( has a severity level of 35, defined below)
    if record["extra"].get("tardis_info_and_above"):
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

logger.add(sys.stdout, level="DEBUG", filter=verbosity_filter)
logger.remove()

showwarning_ = warnings.showwarning


# capturing application warnings
def showwarning(message, *args, **kwargs):
    logger.warning(message)


warnings.showwarning = showwarning

# format of the message
format_ = "  [ <bold><level>{level: <8}</level></bold> ][ <blue>{name}</blue>:<blue>{function}</blue>:<blue>{line}</blue>]- <cyan>{message}</cyan>"

#  adding custom TARDIS INFO Level, just above WARNING
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
