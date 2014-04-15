from numpy import testing
import numpy as np
import pandas as pd
import pytest
from tardis import plasma_array, atomic
from tardis.util import intensity_black_body
from tardis.io.config_reader import TARDISConfigurationNameSpace
import os
import tardis
from astropy import units as u, constants as const

data_path = os.path.join(tardis.__path__[0], 'tests', 'data')
helium_test_db = os.path.join(data_path, 'chianti_he_db.h5')

ion_populations=pd.DataFrame([[2,0,1.0],[2,1,1.0],[2,2,1.0]], columns=['atomic_number', 'ion_number', 0])
ion_populations = ion_populations.set_index(['atomic_number', 'ion_number'])
from astropy import constants as const, units as u
from numpy.testing import assert_allclose

ref_pops = pd.read_hdf(os.path.join(data_path, 'He_nlte_pops.h5'), 'He_level_pops')

def pytest_generate_tests(metafunc):
    # called once per each test function
    funcarglist = metafunc.cls.params[metafunc.function.__name__]
    argnames = list(funcarglist[0])
    metafunc.parametrize(argnames, [[funcargs[name] for name in argnames]
            for funcargs in funcarglist])

class TestNLTE_LTEapprox(object):

    params = {"test_He_ltelevelpops" : [dict(ion_number = 0), dict(ion_number = 1)]}
    
    def setup(self):
        self.nlte_species=[(2,0),(2,1)]
        self.nlte_config = TARDISConfigurationNameSpace({'species':self.nlte_species})
        self.atom_data = atomic.AtomData.from_hdf5(helium_test_db)
        #        self.atom_data.prepare_atom_data([2],nlte_species=self.nlte_species)
        self.plasma = plasma_array.BasePlasmaArray.from_abundance(
            {'He':1.0}, 1e-15*u.Unit('g/cm3'), self.atom_data, 10 * u.day, nlte_config=self.nlte_config)
        self.plasma.j_blues = pd.DataFrame(intensity_black_body(self.atom_data.lines.nu.values[np.newaxis].T, np.array([10000.])))
        self.plasma.tau_sobolevs = pd.DataFrame(np.zeros_like(self.plasma.j_blues))
        self.plasma.t_rads=np.array([10000.])
        self.plasma.t_electrons=np.array([10000.])
        self.plasma.ws=np.array([1.0])
        self.plasma.electron_densities=pd.Series([1.e9])
        self.plasma.ion_populations = ion_populations
        self.plasma.calculate_nlte_level_populations()

    def test_He_ltelevelpops(self, ion_number):
        ion_number = ion_number[0]
        lte_pops = self.atom_data.levels["g"].ix[(2,ion_number)].values * np.exp(- self.atom_data.levels["energy"].ix[(2,ion_number)].values * u.erg / const.k_B / self.plasma.t_rads / u.K).value
        np.testing.assert_allclose(lte_pops, self.atom_data.levels["g"].ix[(2,ion_number)][0]*self.plasma.level_populations[0].ix[(2,ion_number)].values)

class TestNLTE(object):

    params = {"test_He_dilutelevelpops" : [dict(dummy = 0) ],
        "test_He_dilutelevelpops_isnotLTE" : [dict(ion_number = 0), dict(ion_number = 1)]}

    def setup(self):
        self.nlte_species=[(2,0),(2,1)]
        self.nlte_config = TARDISConfigurationNameSpace({'species':self.nlte_species})
        self.atom_data = atomic.AtomData.from_hdf5(helium_test_db)
        self.plasma = plasma_array.BasePlasmaArray.from_abundance(
            {'He':1.0}, 1e-15*u.Unit('g/cm3'), self.atom_data, 10 * u.day, nlte_config=self.nlte_config)
        self.plasma.j_blues = 0.5 * pd.DataFrame(intensity_black_body(self.atom_data.lines.nu.values[np.newaxis].T, np.array([10000.])))
        self.plasma.tau_sobolevs = pd.DataFrame(np.zeros_like(self.plasma.j_blues))
        self.plasma.t_rads=np.array([10000.])
        self.plasma.t_electrons=np.array([9000.])
        self.plasma.ws=np.array([0.5])
        self.plasma.electron_densities=pd.Series([1.e9])
        self.plasma.ion_populations = ion_populations
        self.plasma.calculate_nlte_level_populations()

    def test_He_dilutelevelpops(self, dummy):
        np.testing.assert_allclose(self.plasma.level_populations.values, ref_pops.values)

    def test_He_dilutelevelpops_isnotLTE(self, ion_number):
        ion_number = ion_number[0]
        lte_pops = self.atom_data.levels["g"].ix[(2,ion_number)].values * np.exp(- self.atom_data.levels["energy"].ix[(2,ion_number)].values * u.erg / const.k_B / self.plasma.t_rads / u.K).value
        assert not np.allclose(lte_pops, self.atom_data.levels["g"].ix[(2,ion_number)][0]*self.plasma.level_populations[0].ix[(2,ion_number)].values, atol=0)

"""
atom_model = atomic.AtomData.from_hdf5()

def pytest_generate_tests(metafunc):
    idlist = []
    argvalues = []
    for scenario in metafunc.cls.scenarios:
        idlist.append(scenario[0])
        items = scenario[1].items()
        argnames = [x[0] for x in items]
        argvalues.append(([x[1] for x in items]))
    metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")


def convert_nist_energy(s):
    return float(s.strip().strip('?[]'))


def convert_nist_j(s):
    if '/' in s:
        numerator, denominator = s.split('/')
        return float(numerator) / float(denominator)
    else:
        return float(s)


def read_nist_data(fname):
    data = np.genfromtxt(fname, skip_header=3, delimiter='|', usecols=(2, 3),
        converters={2: convert_nist_j, 3: convert_nist_energy}, names=('j', 'energy'))
    data = data[~np.isnan(data['j'])]
    data = table.Table(data)
    data['energy'].units = units.Unit('eV')
    data['energy'].convert_units_to('erg')

    data = data[~np.isnan(data['energy'])]
    return data

tests_data_dir = os.path.join('tardis', 'tests', 'data')

nist_levels = []

for ion_number in xrange(1, 4):
    nist_levels.append(read_nist_data(os.path.join(tests_data_dir, 'nist_si%d.dat' % ion_number)))

scenarios = []
scenarios.append(('t1000', {'t_rad': 1000}))
scenarios.append(('t5000', {'t_rad': 5000}))
scenarios.append(('t10000', {'t_rad': 10000}))
scenarios.append(('t15000', {'t_rad': 15000}))
scenarios.append(('t20000', {'t_rad': 20000}))


class TestLTEPlasmaCalculations:
    scenarios = scenarios

    def setup_class(self):
        self.nist_partitions = []
        self.nist_phis = []
        self.beta_rad = None
        self.atom_model = None
        self.plasma_model = None
        self.nist_ge = 0

    def test_lte_partition_functions(self, t_rad):
        #g = 2 * j + 1
        del self.nist_partitions[:]
        self.beta_rad = 1 / (constants.cgs.k_B.value * t_rad)
        self.atom_model = atomic.AtomData.from_hdf5()
        self.plasma_model = plasma.LTEPlasma({'Si': 1.}, 1e-8, self.atom_model)
        self.plasma_model.update_radiationfield(t_rad)
        testing.assert_almost_equal(self.plasma_model.beta_rad, self.beta_rad)
        for i in range(len(self.plasma_model.partition_functions[0:3] - 1)):
            nist_level = nist_levels[i].__array__()
            nist_partition = np.sum((2 * nist_level['j'] + 1) * np.exp(-self.beta_rad * nist_level['energy']))
            self.nist_partitions.append(nist_partition)
            partition_delta = abs(nist_partition - self.plasma_model.partition_functions[i]) / nist_partition
            assert partition_delta < 0.05

    def test_lte_saha_calculation(self, t_rad):

        self.beta_rad = 1 / (constants.cgs.k_B.value * t_rad)
        assert len(self.nist_partitions) == 3
        self.nist_ge = ((2 * np.pi * constants.cgs.m_e.value / self.beta_rad) / (constants.cgs.h.value ** 2)) ** 1.5
        testing.assert_almost_equal(self.nist_ge, self.plasma_model.ge)
        i = 0
        self.nist_phis = []
        phis = plasma.calculate_saha()
        for i in phis[0:2]:
            nist_phi_value = self.nist_ge * self.nist_partitions[i] / self.nist_partitions[i + 1]
            nist_phi_value *= np.exp(-self.beta_rad *\
                                     self.atom_model.get_ions(atomic_number)['ionization_energy'][:len(nist_phi_value)])
            self.nist_phis.append(nist_phi_value)
            phi_delta = abs(nist_phi_value - phi[i]) / nist_phi_value
            assert phi_delta <0.05

    def test_ionization_balance(self, t_rad):

        electron_density = 1e09
        phis = plasma.calculate_saha()
        Plasma.calculate_ionization_balance(phis, electron_density)
        nist_phis_product = np.cumprod(self.nist_partitions / electron_density)
        nist.neutral_atom_density = plasma.abundances.ix[atomic_number]['number_density'] / (1 + np.sum(nist_phis_product))
        nist_ion_densities = [nist.neutral_atom_density] + list(nist.neutral_atom_density * nist_phis_product)
        pass

    def test_level_populations(self, t_rad ):
        pass

"""
