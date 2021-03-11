# Licensed under a 3-clause BSD style license - see LICENSE.rst
import sys
import logging
import warnings
from loguru import logger
import contextlib
import astropy
from functools import partialmethod
from numba.core.errors import NumbaPerformanceWarning
import pyne.data


# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *

# ----------------------------------------------------------------------------

from tardis.base import run_tardis
from tardis.io.util import yaml_load_config_file as yaml_load
from tardis.util.custom_logger import logger

warnings.filterwarnings("ignore", category=pyne.utils.QAWarning)
# warnings.filterwarnings("ignore", category=RuntimeWarning)
# warnings.filterwarnings("ignore", category=NumbaPerformanceWarning)
