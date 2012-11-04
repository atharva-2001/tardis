#creating photons

import numpy as np
import constants


class PhotonSource(object):
    pass

np.random.seed(250819801106)


class SimplePhotonSource(PhotonSource):
    #Draw uniform randomly simple photon packets

    @classmethod
    def from_wavelength(cls, wl_start, wl_end, seed=250819801106):
        """Initializing from wavelength
        Parameters
        ----------
        
        wl_start : float
        lower wl
        
        wl_send : float
        upper wl"""

        return cls(constants.c / wl_end / 1e-8, constants.c / wl_start / 1e-8, seed=seed)

    def __init__(self, nu_start, nu_end, seed=250819801106):
        """Initializing photon source
        Parameters
        ----------
        
        nu_start : float
        lower nu_bin
        
        nu_end : float
        upper nu_bin
        """
        self.nu_start = nu_start
        self.nu_end = nu_end
        np.random.seed(seed)

    def __call__(self):
        # returns random frequency and random mu
        return np.random.uniform(self.nu_start, self.nu_end), np.sqrt(np.random.random())


def blackbody_nu(nu, T):
    return ((2 * constants.h * nu ** 3) / (constants.c ** 2)) / (np.exp((constants.h * nu) / (constants.kb * T)) - 1)


def blackbody_lambda(wavelength, T):
    wavelength = wavelength.copy() * 1e-8
    #    return blackbody_nu(constants.c/(wavelength * 1e-8), T)
    return ((2 * constants.h * constants.c ** 2) / wavelength ** 5) / (
        np.exp((constants.h * constants.c) / (wavelength * constants.kb * T)))


def random_blackbody_lambda(T, wl_range=(2000, 12000), size=100):
    wl = np.arange(*wl_range)
    intens = blackbody_lambda(wl, T)
    cum_blackbody = np.cumsum(intens)
    norm_cum_blackbody = cum_blackbody / cum_blackbody.max()
    return wl[norm_cum_blackbody.searchsorted(np.random.random(size))]


def random_blackbody_nu(T, nu_range=(1e8 * constants.c / 5000, 1e8 * constants.c / 9000), sample=int(1e6),
                        size=int(1e6)):
    nu = np.linspace(*nu_range, num=sample)
    intens = blackbody_nu(nu, T)
    cum_blackbody = np.cumsum(intens)
    norm_cum_blackbody = cum_blackbody / cum_blackbody.max()
    return nu[norm_cum_blackbody.searchsorted(np.random.random(size))] + np.random.random(size=size) * (nu[1] - nu[0])