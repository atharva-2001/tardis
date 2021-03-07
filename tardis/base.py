# functions that are important for the general usage of TARDIS
import logging
import warnings
import sys
import pyne.data
from tardis.util.colored_logger import ColoredFormatter, formatter_message
FORMAT = "[$BOLD%(name)-20s$RESET][%(levelname)-18s]  %(message)s ($BOLD%(filename)s$RESET:%(lineno)d)"
COLOR_FORMAT = formatter_message(FORMAT, True)

def run_tardis(
    config, atom_data=None, packet_source=None, simulation_callbacks=[], verbose = 0
):
    """
    This function is one of the core functions to run TARDIS from a given
    config object.

    It will return a model object containing

    Parameters
    ----------
    config : str or dict
        filename of configuration yaml file or dictionary
    atom_data : str or tardis.atomic.AtomData
        if atom_data is a string it is interpreted as a path to a file storing
        the atomic data. Atomic data to use for this TARDIS simulation. If set to None, the
        atomic data will be loaded according to keywords set in the configuration
        [default=None]
    """
    print("RUNNING TARDIS BABY...DEVELOPEMENT MODE...............")

    # default values
    if verbose == 0:
        warnings.filterwarnings("ignore", category=pyne.utils.QAWarning)
        logging.captureWarnings(True)
        logger = logging.getLogger("tardis")
        logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(COLOR_FORMAT)
        console_handler.setFormatter(console_formatter)

        logger.addHandler(console_handler)
        logging.getLogger("py.warnings").addHandler(console_handler)

    if verbose == 1:
        warnings.filterwarnings("ignore", category=pyne.utils.QAWarning)
        logging.captureWarnings(True)
        logger = logging.getLogger("tardis")
        logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(COLOR_FORMAT)
        console_handler.setFormatter(console_formatter)

        logger.addHandler(console_handler)
        # logging.getLogger("py.warnings").addHandler(console_handler)

    if verbose == 2:
        warnings.filterwarnings("ignore", category=pyne.utils.QAWarning)
        logging.captureWarnings(True)
        logger = logging.getLogger("tardis")
        logger.setLevel(logging.ERROR)

        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(COLOR_FORMAT)
        console_handler.setFormatter(console_formatter)

        logger.addHandler(console_handler)
        # logging.getLogger("py.warnings").addHandler(console_handler)


    from tardis.io.config_reader import Configuration
    from tardis.io.atom_data.base import AtomData
    from tardis.simulation import Simulation

    if atom_data is not None:
        try:
            atom_data = AtomData.from_hdf(atom_data)
        except TypeError:
            atom_data = atom_data

    try:
        tardis_config = Configuration.from_yaml(config)
    except TypeError:
        tardis_config = Configuration.from_config_dict(config)

    simulation = Simulation.from_config(
        tardis_config, packet_source=packet_source, atom_data=atom_data
    )
    for cb in simulation_callbacks:
        simulation.add_callback(*cb)

    simulation.run()

    return simulation
