import logging

import numpy as np
import pandas as pd
from numba import njit

from tardis import constants as const
from tardis.plasma.exceptions import PlasmaException
from tardis.plasma.properties.base import (
    Input,
    ProcessingPlasmaProperty,
    TransitionProbabilitiesProperty,
)
from tardis.plasma.properties.continuum_processes.fast_array_util import (
    cumulative_integrate_array_by_blocks,
    numba_cumulative_trapezoid,
)
from tardis.transport.montecarlo.estimators.util import (
    integrate_array_by_blocks,
)

__all__ = [
    "CorrPhotoIonRateCoeff",
    "BfHeatingRateCoeffEstimator",
    "StimRecombCoolingRateCoeffEstimator",
    "SpontRecombCoolingRateCoeff",
    "RawRecombTransProbs",
    "RawPhotoIonTransProbs",
    "CollDeexcRateCoeff",
    "CollExcRateCoeff",
    "RawCollisionTransProbs",
    "AdiabaticCoolingRate",
    "FreeFreeCoolingRate",
    "FreeBoundCoolingRate",
    "LevelNumberDensityLTE",
    "PhotoIonBoltzmannFactor",
    "FreeBoundEmissionCDF",
    "RawTwoPhotonTransProbs",
    "TwoPhotonEmissionCDF",
    "TwoPhotonFrequencySampler",
    "CollIonRateCoeffSeaton",
]

N_A = const.N_A.cgs.value
K_B = const.k_B.cgs.value
C = const.c.cgs.value
H = const.h.cgs.value
A0 = const.a0.cgs.value
M_E = const.m_e.cgs.value
E = const.e.esu.value
BETA_COLL = (H**4 / (8 * K_B * M_E**3 * np.pi**3)) ** 0.5
F_K = (
    16
    / (3.0 * np.sqrt(3))
    * np.sqrt((2 * np.pi) ** 3 * K_B / (H**2 * M_E**3))
    * (E**2 / C) ** 3
)  # See Eq. 19 in Sutherland, R. S. 1998, MNRAS, 300, 321
FF_OPAC_CONST = (
    (2 * np.pi / (3 * M_E * K_B)) ** 0.5 * 4 * E**6 / (3 * M_E * H * C)
)  # See Eq. 6.1.8 in http://personal.psu.edu/rbc3/A534/lec6.pdf

logger = logging.getLogger(__name__)


def get_ion_multi_index(multi_index_full, next_higher=True):
    """
    Calculate the corresponding ion MultiIndex for a level MultiIndex.

    Parameters
    ----------
    multi_index_full : pandas.MultiIndex (atomic_number, ion_number,
                                          level_number)
    next_higher : bool, default True
        If True use ion number of next higher ion, else use ion_number from
        multi_index_full.

    Returns
    -------
    pandas.MultiIndex (atomic_number, ion_number)
       Ion MultiIndex for the given level MultiIndex.
    """
    atomic_number = multi_index_full.get_level_values(0)
    ion_number = multi_index_full.get_level_values(1)
    if next_higher is True:
        ion_number += 1
    return pd.MultiIndex.from_arrays([atomic_number, ion_number])


def get_ground_state_multi_index(multi_index_full):
    """
    Calculate the ground-state MultiIndex for the next higher ion.

    Parameters
    ----------
    multi_index_full : pandas.MultiIndex (atomic_number, ion_number,
                                          level_number)

    Returns
    -------
    pandas.MultiIndex (atomic_number, ion_number)
        Ground-state MultiIndex for the next higher ion.
    """
    atomic_number = multi_index_full.get_level_values(0)
    ion_number = multi_index_full.get_level_values(1) + 1
    level_number = np.zeros_like(ion_number)
    return pd.MultiIndex.from_arrays([atomic_number, ion_number, level_number])


def cooling_rate_series2dataframe(cooling_rate_series, destination_level_idx):
    """
    Transform cooling-rate Series to DataFrame.

    This function transforms a Series with cooling rates into
    an indexed DataFrame that can be used in MarkovChainTransProbs.

    Parameters
    ----------
    cooling_rate_series : pandas.Series, dtype float
        Cooling rates for a process with a single destination idx.
        Examples are adiabatic cooling or free-free cooling.
    destination_level_idx : str
        Destination idx of the cooling process; for example
        'adiabatic' for adiabatic cooling.

    Returns
    -------
    cooling_rate_frame : pandas.DataFrame, dtype float
        Indexed by source_level_idx, destination_level_idx, transition_type
        for the use in MarkovChainTransProbs.
    """
    index_names = [
        "source_level_idx",
        "destination_level_idx",
        "transition_type",
    ]
    index = pd.MultiIndex.from_tuples(
        [("k", destination_level_idx, -1)], names=index_names
    )
    cooling_rate_frame = pd.DataFrame(
        cooling_rate_series.values[np.newaxis], index=index
    )
    return cooling_rate_frame


class IndexSetterMixin:
    @staticmethod
    def set_index(p, photo_ion_idx, transition_type=0, reverse=True):
        idx = photo_ion_idx.loc[p.index]
        transition_type = transition_type * np.ones_like(
            idx.destination_level_idx
        )
        transition_type = pd.Series(transition_type, name="transition_type")
        idx_arrays = [idx.source_level_idx, idx.destination_level_idx]
        if reverse:
            idx_arrays = idx_arrays[::-1]
        idx_arrays.append(transition_type)
        index = pd.MultiIndex.from_arrays(idx_arrays)
        if reverse:
            index.names = index.names[:-1][::-1] + [index.names[-1]]
        p = p.set_index(index, drop=True)
        return p


class SpontRecombCoolingRateCoeff(ProcessingPlasmaProperty):
    """
    Attributes
    ----------
    c_fb_sp : pandas.DataFrame, dtype float
        The rate coefficient for cooling by
        spontaneous recombination.
    """

    outputs = ("c_fb_sp",)
    latex_name = (r"c^{\textrm{sp}}_{\textrm{fb}}",)

    def calculate(
        self,
        photo_ion_cross_sections,
        t_electrons,
        photo_ion_block_references,
        photo_ion_index,
        phi_ik,
        nu_i,
        boltzmann_factor_photo_ion,
    ):
        x_sect = photo_ion_cross_sections["x_sect"].values
        nu = photo_ion_cross_sections["nu"].values
        factor = (1 - nu_i / photo_ion_cross_sections["nu"]).values
        alpha_sp = (8 * np.pi * x_sect * factor * nu**3 / C**2) * H
        alpha_sp = alpha_sp[:, np.newaxis]
        alpha_sp = alpha_sp * boltzmann_factor_photo_ion
        alpha_sp = integrate_array_by_blocks(
            alpha_sp, nu, photo_ion_block_references
        )
        alpha_sp = pd.DataFrame(alpha_sp, index=photo_ion_index)
        return alpha_sp * phi_ik.loc[alpha_sp.index]


class FreeBoundEmissionCDF(ProcessingPlasmaProperty):
    """
    Attributes
    ----------
    fb_emission_cdf : pandas.DataFrame, dtype float
        The cumulative distribution function (CDF) for the frequencies of
        energy packets emitted in free-bound transitions. The tabulated CDF
        is used to sample packet frequencies in the Monte Carlo simulation.
        We use the same CDF for free-bound emission from k- and i-packets
        (in contrast to ARTIS).
    """

    outputs = ("fb_emission_cdf",)
    latex_name = (r"P(\nu_{bf, emission}) \leq \nu)",)

    def calculate(
        self,
        photo_ion_cross_sections,
        t_electrons,
        photo_ion_block_references,
        photo_ion_index,
        nu_i,
        boltzmann_factor_photo_ion,
    ):
        x_sect = photo_ion_cross_sections["x_sect"].values
        nu = photo_ion_cross_sections["nu"].values
        # alpha_sp_E will be missing a lot of prefactors since we are only
        # interested in relative values here
        alpha_sp_E = nu**3 * x_sect
        alpha_sp_E = alpha_sp_E[:, np.newaxis]
        alpha_sp_E = alpha_sp_E * boltzmann_factor_photo_ion
        alpha_sp_E = cumulative_integrate_array_by_blocks(
            alpha_sp_E, nu, photo_ion_block_references
        )
        fb_emission_cdf = pd.DataFrame(
            alpha_sp_E, index=photo_ion_cross_sections.index
        )
        return fb_emission_cdf


class RawRecombTransProbs(TransitionProbabilitiesProperty, IndexSetterMixin):
    """
    Attributes
    ----------
    p_recomb : pandas.DataFrame, dtype float
        The unnormalized transition probabilities for
        spontaneous recombination.
    """

    outputs = ("p_recomb",)
    transition_probabilities_outputs = ("p_recomb",)
    latex_name = (r"p^{\textrm{recomb}}",)

    def calculate(self, alpha_sp, nu_i, energy_i, photo_ion_idx):
        p_recomb_deactivation = alpha_sp.multiply(nu_i, axis=0) * H
        p_recomb_deactivation = self.set_index(
            p_recomb_deactivation, photo_ion_idx, transition_type=-1
        )

        p_recomb_internal = alpha_sp.multiply(energy_i, axis=0)
        p_recomb_internal = self.set_index(
            p_recomb_internal, photo_ion_idx, transition_type=0
        )
        p_recomb = pd.concat([p_recomb_deactivation, p_recomb_internal])
        return p_recomb


class RawPhotoIonTransProbs(TransitionProbabilitiesProperty, IndexSetterMixin):
    """
    Attributes
    ----------
    p_photo_ion : pandas.DataFrame, dtype float
        The unnormalized transition probabilities for
        radiative ionization.
    """

    outputs = ("p_photo_ion",)
    transition_probabilities_outputs = ("p_photo_ion",)
    latex_name = (r"p^{\textrm{photo_ion}}",)

    def calculate(self, gamma_corr, energy_i, photo_ion_idx):
        p_photo_ion = gamma_corr.multiply(energy_i, axis=0)
        p_photo_ion = self.set_index(p_photo_ion, photo_ion_idx, reverse=False)
        return p_photo_ion


class CorrPhotoIonRateCoeff(ProcessingPlasmaProperty):
    """
    Attributes
    ----------
    gamma_corr : pandas.DataFrame, dtype float
        The rate coefficient for radiative ionization corrected for
        stimulated recombination.
    """

    outputs = ("gamma_corr",)
    latex_name = (r"\gamma_\mathrm{corr}",)

    def calculate(
        self,
        gamma,
        alpha_stim,
        electron_densities,
        ion_number_density,
        level_number_density,
    ):
        n_k_index = get_ion_multi_index(alpha_stim.index)
        n_k = ion_number_density.loc[n_k_index].values
        n_i = level_number_density.loc[alpha_stim.index].values
        gamma_corr = gamma - (alpha_stim * n_k / n_i).multiply(
            electron_densities
        )
        num_neg_elements = (gamma_corr < 0).sum().sum()
        if num_neg_elements:
            raise PlasmaException(
                "Negative values in CorrPhotoIonRateCoeff.  Try raising the number of montecarlo packets."
            )
        return gamma_corr


class PhotoIonEstimatorsNormFactor(ProcessingPlasmaProperty):
    outputs = ("photo_ion_norm_factor",)
    latex_name = (r"\frac{1}{t_\textrm{simulation volume h}}",)

    @staticmethod
    def calculate(time_simulation, volume):
        return (time_simulation * volume * H) ** -1


class StimRecombCoolingRateCoeffEstimator(Input):
    """
    Attributes
    ----------
    stim_recomb_cooling_coeff_estimator : pandas.DataFrame, dtype float
        Unnormalized MC estimator for the stimulated recombination cooling rate
        coefficient.
    """

    outputs = ("stim_recomb_cooling_coeff_estimator",)


class BfHeatingRateCoeffEstimator(Input):
    """
    Attributes
    ----------
    bf_heating_coeff_estimator : pandas.DataFrame, dtype float
        Unnormalized MC estimator for the rate
        coefficient for bound-free heating.
    """

    outputs = ("bf_heating_coeff_estimator",)
    latex_name = (r"h_\textrm{bf}_\textrm{estim}",)


class CollExcRateCoeff(ProcessingPlasmaProperty):
    """
    Attributes
    ----------
    coll_exc_coeff : pandas.DataFrame, dtype float
        Rate coefficient for collisional excitation.
    """

    outputs = ("coll_exc_coeff",)
    latex_name = ("c_{lu}",)

    def calculate(self, yg_interp, yg_index, t_electrons, delta_E_yg):
        yg = yg_interp(t_electrons)
        boltzmann_factor = np.exp(
            -delta_E_yg.values[np.newaxis].T / (t_electrons * K_B)
        )
        q_ij = (
            BETA_COLL / np.sqrt(t_electrons) * yg * boltzmann_factor
        )  # see formula A2 in Przybilla, Butler 2004 - Apj 609, 1181
        return pd.DataFrame(q_ij, index=yg_index)


class CollDeexcRateCoeff(ProcessingPlasmaProperty):
    """
    Attributes
    ----------
    coll_deexc_coeff : pandas.DataFrame, dtype float
        Rate coefficient for collisional deexcitation.
    """

    outputs = ("coll_deexc_coeff",)
    latex_name = ("c_{ul}",)

    def calculate(self, thermal_lte_level_boltzmann_factor, coll_exc_coeff):
        level_lower_index = coll_exc_coeff.index.droplevel("level_number_upper")
        level_upper_index = coll_exc_coeff.index.droplevel("level_number_lower")

        n_lower_prop = thermal_lte_level_boltzmann_factor.loc[
            level_lower_index
        ].values
        n_upper_prop = thermal_lte_level_boltzmann_factor.loc[
            level_upper_index
        ].values

        coll_deexc_coeff = coll_exc_coeff * n_lower_prop / n_upper_prop
        return coll_deexc_coeff


class RawCollisionTransProbs(TransitionProbabilitiesProperty, IndexSetterMixin):
    """
    Attributes
    ----------
    p_coll : pandas.DataFrame, dtype float
        The unnormalized transition probabilities for
        collisional excitation.
    """

    outputs = ("p_coll",)
    transition_probabilities_outputs = ("p_coll",)
    latex_name = (r"p^{\textrm{coll}}",)

    def calculate(
        self,
        coll_exc_coeff,
        coll_deexc_coeff,
        yg_idx,
        electron_densities,
        delta_E_yg,
        atomic_data,
        level_number_density,
    ):
        p_deexc_deactivation = (coll_deexc_coeff * electron_densities).multiply(
            delta_E_yg.values, axis=0
        )
        p_deexc_deactivation = self.set_index(
            p_deexc_deactivation, yg_idx, reverse=True
        )
        p_deexc_deactivation = p_deexc_deactivation.groupby(level=[0]).sum()
        index_dd = pd.MultiIndex.from_product(
            [p_deexc_deactivation.index.values, ["k"], [0]],
            names=list(yg_idx.columns) + ["transition_type"],
        )
        p_deexc_deactivation = p_deexc_deactivation.set_index(index_dd)

        level_lower_index = coll_deexc_coeff.index.droplevel(
            "level_number_upper"
        )
        energy_lower = atomic_data.levels.energy.loc[level_lower_index]
        p_deexc_internal = (coll_deexc_coeff * electron_densities).multiply(
            energy_lower.values, axis=0
        )
        p_deexc_internal = self.set_index(
            p_deexc_internal, yg_idx, transition_type=0, reverse=True
        )

        p_exc_internal = (coll_exc_coeff * electron_densities).multiply(
            energy_lower.values, axis=0
        )
        p_exc_internal = self.set_index(
            p_exc_internal, yg_idx, transition_type=0, reverse=False
        )
        p_exc_cool = (coll_exc_coeff * electron_densities).multiply(
            delta_E_yg.values, axis=0
        )
        p_exc_cool = (
            p_exc_cool * level_number_density.loc[level_lower_index].values
        )
        p_exc_cool = self.set_index(p_exc_cool, yg_idx, reverse=False)
        p_exc_cool = p_exc_cool.groupby(level="destination_level_idx").sum()
        exc_cool_index = pd.MultiIndex.from_product(
            [["k"], p_exc_cool.index.values, [0]],
            names=list(yg_idx.columns) + ["transition_type"],
        )
        p_exc_cool = p_exc_cool.set_index(exc_cool_index)
        p_coll = pd.concat(
            [p_deexc_deactivation, p_deexc_internal, p_exc_internal, p_exc_cool]
        )
        return p_coll


class RawTwoPhotonTransProbs(TransitionProbabilitiesProperty, IndexSetterMixin):
    """
    Attributes
    ----------
    p_two_photon : pandas.DataFrame, dtype float
        The unnormalized transition probabilities for two photon decay.
    """

    outputs = ("p_two_photon",)
    transition_probabilities_outputs = ("p_two_photon",)

    def calculate(self, two_photon_data, two_photon_idx, density):
        no_shells = len(density)
        p_two_phot = two_photon_data.A_ul * two_photon_data.nu0 * H
        p_two_phot = pd.concat([p_two_phot] * no_shells, axis=1)
        # TODO: In principle there could be internal two photon transitions
        p_two_phot = self.set_index(
            p_two_phot,
            two_photon_idx,
            transition_type=-1,
            reverse=False,
        )
        p_two_phot.index = p_two_phot.index.set_levels(
            ["two-photon"], level="destination_level_idx"
        )
        return p_two_phot


class TwoPhotonEmissionCDF(ProcessingPlasmaProperty):
    """
    Attributes
    ----------
    two_photon_emission_cdf : pandas.DataFrame, dtype float
        The cumulative distribution function (CDF) for the frequencies of
        energy packets emitted in two photon transitions. The tabulated CDF
        is used to sample packet frequencies in the Monte Carlo simulation.
    """

    outputs = ("two_photon_emission_cdf",)

    def calculate(self, two_photon_data):
        bins = 500
        # The number of two photon transitions is very small
        # and the CDF has to be calculated only once.
        # There is no need to vectorize the calculation.
        emission_cdfs = []
        for index, row in two_photon_data.iterrows():
            alpha = row.alpha
            beta = row.beta
            gamma = row.gamma
            nu = np.linspace(0.0, row.nu0, bins)
            y = nu / row.nu0
            j_nu = self.calculate_j_nu(y, alpha, beta, gamma)

            cdf = np.zeros_like(nu)
            cdf[1:] = numba_cumulative_trapezoid(j_nu, nu)
            cdf /= cdf[-1]
            index_cdf = pd.MultiIndex.from_tuples([index] * bins)
            cdf = pd.DataFrame({"nu": nu, "cdf": cdf}, index=index_cdf)
            emission_cdfs.append(cdf)
        return pd.concat(emission_cdfs)

    @staticmethod
    def calculate_j_nu(y, alpha, beta, gamma):
        """
        Calculate two photon emissivity.

        This function calculates the two photon emissivity in the frequency
        scale based on Eq. 2 and Eq. 3 in Nussbaumer & Schmutz (1984). The
        emissivity is not normalized since it is only used to calculate
        relative emission probabilities.

        Parameters
        ----------
        y : numpy.ndarray, dtype float
            Emission frequency divided by that of the normal line
            transition corresponding to the two photon decay.
        alpha : float
            Fit coefficient.
        beta : float
            Fit coefficient.
        gamma : float
            Fit coefficient.

        Returns
        -------
        numpy.ndarray, dtype float
            Unnormalized two photon emissivity in the frequency scale.
        """
        ay = y * (1 - y) * (1 - (4 * y * (1 - y)) ** gamma)
        ay += alpha * (y * (1 - y)) ** beta * (4 * y * (1 - y)) ** gamma
        j_nu = ay * y
        return j_nu


class AdiabaticCoolingRate(TransitionProbabilitiesProperty):
    """
    Attributes
    ----------
    cool_rate_adiabatic : pandas.DataFrame, dtype float
        The adiabatic cooling rate of the electron gas.
    """

    outputs = ("cool_rate_adiabatic",)
    transition_probabilities_outputs = ("cool_rate_adiabatic",)
    latex_name = (r"C_{\textrm{adiabatic}}",)

    def calculate(self, electron_densities, t_electrons, time_explosion):
        cool_rate_adiabatic = (
            3.0 * electron_densities * K_B * t_electrons
        ) / time_explosion

        cool_rate_adiabatic = cooling_rate_series2dataframe(
            cool_rate_adiabatic, destination_level_idx="adiabatic"
        )
        return cool_rate_adiabatic


class FreeFreeCoolingRate(TransitionProbabilitiesProperty):
    """
    Attributes
    ----------
    cool_rate_ff : pandas.DataFrame, dtype float
        The free-free cooling rate of the electron gas.
    ff_cooling_factor : pandas.Series, dtype float
        Pre-factor needed in the calculation of the free-free cooling rate and
        the free-free opacity.

    Notes
    -----
    This implementation uses a free-free Gaunt factor of one for all species
    and ionization stages, which is an approximation.
    """

    outputs = ("cool_rate_ff", "ff_cooling_factor")
    transition_probabilities_outputs = ("cool_rate_ff",)
    latex_name = (r"C^{\textrm{ff}}",)

    def calculate(self, ion_number_density, electron_densities, t_electrons):
        ff_cooling_factor = self._calculate_ff_cooling_factor(
            ion_number_density, electron_densities
        )
        cool_rate_ff = F_K * np.sqrt(t_electrons) * ff_cooling_factor
        cool_rate_ff = cooling_rate_series2dataframe(
            cool_rate_ff, destination_level_idx="ff"
        )
        return cool_rate_ff, ff_cooling_factor.values

    @staticmethod
    def _calculate_ff_cooling_factor(ion_number_density, electron_densities):
        ion_charge = ion_number_density.index.get_level_values(1).values
        factor = (
            electron_densities
            * ion_number_density.multiply(ion_charge**2, axis=0).sum()
        )
        return factor


class TwoPhotonFrequencySampler(ProcessingPlasmaProperty):
    """
    Attributes
    ----------
    nu_two_photon_sampler : float
        Frequency of the two-photon emission process
    """

    outputs = ("nu_two_photon_sampler",)

    def calculate(self, two_photon_emission_cdf):
        nus = two_photon_emission_cdf["nu"].values
        em = two_photon_emission_cdf["cdf"].values

        @njit(error_model="numpy", fastmath=True)
        def nu_two_photon():
            zrand = np.random.random()
            idx = np.searchsorted(em, zrand, side="right")

            return nus[idx] - (em[idx] - zrand) / (em[idx] - em[idx - 1]) * (
                nus[idx] - nus[idx - 1]
            )

        return nu_two_photon


class FreeBoundCoolingRate(TransitionProbabilitiesProperty):
    """
    Attributes
    ----------
    cool_rate_fb_total : pandas.DataFrame, dtype float
        The total free-bound cooling rate of the electron gas.
    cool_rate_fb : pandas.DataFrame, dtype float
        The individual free-bound cooling rates of the electron gas.
    p_fb_deactivation: pandas.DataFrame, dtype float
        Probabilities of free-bound cooling in a specific continuum
        (identified by its continuum_idx).
    """

    outputs = ("cool_rate_fb_tot", "cool_rate_fb", "p_fb_deactivation")
    transition_probabilities_outputs = ("cool_rate_fb_tot",)
    latex_name = (r"C^{\textrm{fb, tot}}", r"C^{\textrm{fb}}")

    def calculate(
        self,
        c_fb_sp,
        electron_densities,
        ion_number_density,
        level2continuum_idx,
    ):
        next_ion_stage_index = get_ion_multi_index(c_fb_sp.index)
        n_k = ion_number_density.loc[next_ion_stage_index]

        cool_rate_fb = c_fb_sp.multiply(electron_densities, axis=1) * n_k.values
        cool_rate_fb_tot = cooling_rate_series2dataframe(
            cool_rate_fb.sum(axis=0), "bf"
        )

        p_fb_deactivation = cool_rate_fb / cool_rate_fb_tot.values
        # TODO: this will be needed more often; put it in a function
        continuum_idx = level2continuum_idx.loc[p_fb_deactivation.index].values
        p_fb_deactivation = p_fb_deactivation.set_index(
            continuum_idx
        ).sort_index(ascending=True)
        p_fb_deactivation.index.name = "continuum_idx"
        return cool_rate_fb_tot, cool_rate_fb, p_fb_deactivation


class LevelNumberDensityLTE(ProcessingPlasmaProperty):
    """
    Attributes
    ----------
    lte_level_number_density : pandas.DataFrame, dtype float
    """

    outputs = ("lte_level_number_density",)
    latex_name = (r"n_{\textrm{i}}^*",)

    # TODO: only do this for continuum species
    def calculate(self, electron_densities, phi_ik, ion_number_density):
        next_higher_ion_index = get_ion_multi_index(
            phi_ik.index, next_higher=True
        )
        # TODO: Check that n_k is correct (and not n_k*)
        lte_level_number_density = (
            phi_ik * ion_number_density.loc[next_higher_ion_index].values
        ).multiply(electron_densities, axis=1)
        return lte_level_number_density


class PhotoIonBoltzmannFactor(ProcessingPlasmaProperty):
    """
    Attributes
    ----------
    boltzmann_factor_photo_ion : pandas.DataFrame, dtype float
    """

    outputs = ("boltzmann_factor_photo_ion",)

    @staticmethod
    def calculate(photo_ion_cross_sections, t_electrons):
        nu = photo_ion_cross_sections["nu"].values

        boltzmann_factor = np.exp(-nu[np.newaxis].T / t_electrons * (H / K_B))
        return boltzmann_factor


class CollIonRateCoeffSeaton(ProcessingPlasmaProperty):
    """
    Attributes
    ----------
    coll_ion_coeff : pandas.DataFrame, dtype float
        The rate coefficient for collisional ionization in the Seaton
        approximation. Multiply with the electron density and the
        level number density to obtain the total rate.

    Notes
    -----
    The rate coefficient for collisional ionization in the Seaton approximation
    is calculated according to Eq. 9.60 in [1].

    References
    ----------
    .. [1] Hubeny, I. and Mihalas, D., "Theory of Stellar Atmospheres". 2014.
    """

    outputs = ("coll_ion_coeff",)
    latex_name = (r"c_{\textrm{i,}\kappa}",)

    def calculate(self, photo_ion_cross_sections, t_electrons):
        photo_ion_cross_sections_threshold = photo_ion_cross_sections.groupby(
            level=[0, 1, 2]
        ).first()
        nu_i = photo_ion_cross_sections_threshold["nu"]
        factor = self._calculate_factor(nu_i, t_electrons)
        coll_ion_coeff = 1.55e13 * photo_ion_cross_sections_threshold["x_sect"]
        coll_ion_coeff = factor.multiply(coll_ion_coeff, axis=0)
        coll_ion_coeff = coll_ion_coeff.divide(np.sqrt(t_electrons), axis=1)

        ion_number = coll_ion_coeff.index.get_level_values("ion_number").values
        coll_ion_coeff[ion_number == 0] *= 0.1
        coll_ion_coeff[ion_number == 1] *= 0.2
        coll_ion_coeff[ion_number >= 2] *= 0.3
        return coll_ion_coeff

    def _calculate_factor(self, nu_i, t_electrons):
        u0s = self._calculate_u0s(nu_i.values, t_electrons)
        factor = np.exp(-u0s) / u0s
        factor = pd.DataFrame(factor, index=nu_i.index)
        return factor

    @staticmethod
    def _calculate_u0s(nu, t_electrons):
        u0s = nu[np.newaxis].T / t_electrons * (H / K_B)
        return u0s
