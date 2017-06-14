import logging
import pandas as pd
import numpy as np

from tardis.plasma.properties.base import ProcessingPlasmaProperty

logger = logging.getLogger(__name__)

__all__ = ['LevelNumberDensity', 'LevelNumberDensityHeNLTE']

class LevelNumberDensity(ProcessingPlasmaProperty):
    """
    Attributes:
    level_number_density : Pandas DataFrame, dtype float
                           Index atom number, ion number, level number. Columns are zones.
    """
    outputs = ('level_number_density',)
    latex_name = ('N_{i,j,k}',)
    latex_formula = ('N_{i,j}\\dfrac{bf_{i,j,k}}{Z_{i,j}}',)

    def __init__(self, plasma_parent):
        """
        Calculates the level populations with the Boltzmann equation in LTE.
        """
        super(LevelNumberDensity, self).__init__(plasma_parent)
        self._update_inputs()
        self.initialize_indices = True

    def _initialize_indices(self, levels, partition_function):
        indexer = pd.Series(np.arange(partition_function.shape[0]),
                            index=partition_function.index)
        self._ion2level_idx = indexer.ix[levels.droplevel(2)].values

    def calculate(self, level_boltzmann_factor, ion_number_density,
        levels, partition_function):
        """
        Reduces non-metastable level populations by a factor of W compared to LTE in the case of dilute-lte excitation.
        """
        if self.initialize_indices:
            self._initialize_indices(levels, partition_function)
            self.initialize_indices = False
        partition_function_broadcast = partition_function.values[
            self._ion2level_idx]
        level_population_fraction = (level_boltzmann_factor.values
                                     / partition_function_broadcast)
        ion_number_density_broadcast = ion_number_density.values[
            self._ion2level_idx]
        level_number_density = (level_population_fraction *
                                ion_number_density_broadcast)
        return pd.DataFrame(level_number_density,
                            index=level_boltzmann_factor.index)

class LevelNumberDensityHeNLTE(LevelNumberDensity):
    """
    Attributes:
    level_number_density : Pandas DataFrame, dtype float
                           Index atom number, ion number, level number. Columns are zones.
    """

    def calculate(self, level_boltzmann_factor,
        ion_number_density, levels, partition_function,
                               helium_population_updated):
        """
        If one of the two helium NLTE methods is used, this updates the helium level populations to the appropriate
        values.
        """
        level_number_density = super(LevelNumberDensityHeNLTE, self).calculate(
            level_boltzmann_factor, ion_number_density, levels,
            partition_function)
        if helium_population_updated is not None:
            level_number_density.ix[2].update(helium_population_updated)
        return level_number_density
