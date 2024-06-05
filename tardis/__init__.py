# Licensed under a 3-clause BSD style license - see LICENSE.rst

# Packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *

# ----------------------------------------------------------------------------

__all__ = []

# ----------------------------------------------------------------------------

import sys
import warnings

# ----------------------------------------------------------------------------

TARDIS_PATH = __path__

if ("astropy.units" in sys.modules) or ("astropy.constants" in sys.modules):
    warnings.warn(
        "Astropy is already imported externally. Astropy should be imported"
        " after TARDIS."
    )
else:
    from astropy import astronomical_constants, physical_constants

    physical_constants.set("codata2014")
    astronomical_constants.set("iau2012")

# ----------------------------------------------------------------------------

from tardis.base import run_tardis
from tardis.io.util import yaml_load_file as yaml_load
