from tardis.util.colored_logger import ColoredFormatter, formatter_message
from loguru import logger
from functools import partialmethod
import logging
import sys

# FORMAT = "[$BOLD%(name)-20s$RESET][%(levelname)-18s]  %(message)s ($BOLD%(filename)s$RESET:%(lineno)d)"
# COLOR_FORMAT = formatter_message(FORMAT, True)

logger.__class__.special_info = partialmethod(
    logger.__class__.log, "special_info", no=35
)

logger.add(sys.stderr, level="DEBUG")
logger.remove()


def verbosity_filter(record):
    if record["extra"].get("warn_and_above"):
        return record["level"].no >= logger.level("WARNING").no

    if record["extra"].get("info_and_above"):
        return record["level"].no >= logger.level("INFO").no

    if record["extra"].get("tardis_info_and_above"):
        return record["level"].no >= logger.level("TARDIS INFO").no

    return True


logger.level("TARDIS INFO", no=35, color="<blue>")
logger.__class__.tardis_info = partialmethod(
    logger.__class__.log,
    "TARDIS INFO",
)

logger.add(
    sys.stderr,
    filter=verbosity_filter,
    level="DEBUG",
)
