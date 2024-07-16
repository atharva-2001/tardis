import logging
import sys
from ipywidgets import Output, Tab, Layout
from IPython.display import display

from tardis.io.logger.colored_logger import ColoredFormatter

logging.captureWarnings(True)
logger = logging.getLogger("tardis")

# Create Output widgets for each log level
log_outputs = {
    "WARNING/ERROR": Output(layout=Layout(height='300px', overflow_y='auto')),
    "INFO": Output(layout=Layout(height='300px', overflow_y='auto')),
    "DEBUG": Output(layout=Layout(height='300px', overflow_y='auto')),
}

# Create a Tab widget to hold the Output widgets
tab = Tab(children=[log_outputs["WARNING/ERROR"], log_outputs["INFO"], log_outputs["DEBUG"]])
tab.set_title(0, "WARNING/ERROR")
tab.set_title(1, "INFO")
tab.set_title(2, "DEBUG")

display(tab)

class WidgetHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def emit(self, record):
        log_entry = self.format(record)
        if record.levelno in (logging.WARNING, logging.ERROR):
            with log_outputs["WARNING/ERROR"]:
                print(log_entry)
        elif record.levelno == logging.INFO:
            with log_outputs["INFO"]:
                print(log_entry)
        elif record.levelno == logging.DEBUG:
            with log_outputs["DEBUG"]:
                print(log_entry)

# Setup widget handler
widget_handler = WidgetHandler()
widget_handler.setFormatter(ColoredFormatter()) #TODO: Make ColoredFormatter work

logger.addHandler(widget_handler)
logging.getLogger("py.warnings").addHandler(widget_handler)

LOGGING_LEVELS = {
    "NOTSET": logging.NOTSET,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    #"CRITICAL": logging.CRITICAL,
}
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_SPECIFIC_STATE = False


class FilterLog:
    """
    Filter Log Class for Filtering Logging Output
    to a particular level

    Parameters
    ----------
    log_level : logging object
        allows to have a filter for the
        particular log_level
    """

    def __init__(self, log_levels):
        self.log_levels = log_levels

    def filter(self, log_record):
        """
        filter() allows to set the logging level for
        all the record that are being parsed & hence remove those
        which are not of the particular level

        Parameters
        ----------
        log_record : logging.record
            which the particular record upon which the
            filter will be applied

        Returns
        -------
        boolean : True, if the current log_record has the
            level that of the specified log_level
            False, if the current log_record doesn't have the
            same log_level as the specified one
        """
        return log_record.levelno in self.log_levels


def logging_state(log_level, tardis_config, specific_log_level):
    """
    Function to set the logging configuration for the simulation output
    Called from within run_tardis()
    Configured via functional arguments passed through run_tardis() - log_level & specific_log_level
    Configured via YAML parameters under `debug` section - log_level & specific_log_level

    Parameters
    ----------
    log_level: str
        Allows to input the log level for the simulation
        Uses Python logging framework to determine the messages that will be output
    specific_log_level: boolean
        Allows to set specific logging levels. Logs of the `log_level` level would be output.
    """
    if "debug" in tardis_config:
        specific_log_level = (
            tardis_config["debug"]["specific_log_level"]
            if specific_log_level is None
            else specific_log_level
        )

        logging_level = (
            log_level if log_level else tardis_config["debug"]["log_level"]
        )

        # Displays a message when both log_level & tardis["debug"]["log_level"] are specified
        if log_level and tardis_config["debug"]["log_level"]:
            print(
                "log_level is defined both in Functional Argument & YAML Configuration {debug section}"
            )
            print(
                f"log_level = {log_level.upper()} will be used for Log Level Determination\n"
            )

    else:
        # Adds empty `debug` section for the YAML
        tardis_config["debug"] = {}

        if log_level:
            logging_level = log_level
        else:
            tardis_config["debug"]["log_level"] = DEFAULT_LOG_LEVEL
            logging_level = tardis_config["debug"]["log_level"]

        if not specific_log_level:
            tardis_config["debug"][
                "specific_log_level"
            ] = DEFAULT_SPECIFIC_STATE
            specific_log_level = tardis_config["debug"]["specific_log_level"]

    logging_level = logging_level.upper()
    if logging_level not in LOGGING_LEVELS:
        raise ValueError(
            f"Passed Value for log_level = {logging_level} is Invalid. Must be one of the following {list(LOGGING_LEVELS.keys())}"
        )

    # Getting the TARDIS logger & all its children loggers
    logger = logging.getLogger("tardis")

    # Creating a list for Storing all the Loggers which are derived from TARDIS
    tardis_loggers = tardis_logger()

    if logging_level in LOGGING_LEVELS:
        for logger in tardis_loggers:
            logger.setLevel(LOGGING_LEVELS[logging_level])

    if logger.filters:
        for filter in logger.filters:
            for logger in tardis_loggers:
                logger.removeFilter(filter)

    if specific_log_level:
        filter_log = FilterLog([LOGGING_LEVELS[logging_level], logging.INFO, logging.DEBUG])
        for logger in tardis_loggers:
            logger.addFilter(filter_log)
    else:
        for filter in logger.filters:
            for logger in tardis_loggers:
                logger.removeFilter(filter)


def tardis_logger():
    """
    Generates the list of the loggers which are derived from TARDIS
    All loggers which are of the form `tardis.module_name` are added to the list

    Parameters
    ----------
    list_for_loggers : list
        List for storing the loggers derived from TARDIS

    Returns
    -------
    list_for_loggers : list
    """
    list_for_loggers = []
    for name in logging.root.manager.loggerDict:
        if not name.find("tardis"):
            list_for_loggers.append(logging.getLogger(name))
    return list_for_loggers
