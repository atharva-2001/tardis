import astropy.units as u
import tardis.constants as const
import numpy as np
import scipy.linalg as linalg
import pandas as pd

M_E = const.m_e.cgs.value
H = const.h.cgs.value
H_BAR = const.hbar.cgs.value
E_CHARGE = const.e.esu.value
K_B = const.k_B.to("eV / K").value
C_LIGHT = const.c.cgs.value
EV2ERG = u.eV.to(u.erg)
H_ION_POTENTIAL = M_E * C_LIGHT ** 2
A0 = const.a0.cgs.value

# Eqn 7 set up energy grid, bin-wise integration, multiply S(E) by the energy grid
class Energy_Grid:
    def __init__(self, energy_min, energy_max, points):
        self.size = points
        self.energy_min = energy_min
        self.energy_max = energy_max
        self.grid = np.linspace(energy_min, energy_max, num=points)
        self.delta_energy = self.grid[1] - self.grid[0]


# Already in TARDIS but need to make sure hitting the format
def compute_lte_populations(atomic_levels, ions, ion_populations, temperature):
    population_list = []
    lte_populations = pd.DataFrame(
        population_list,
        columns=[
            "atomic_number",
            "ion_number",
            "level",
            "n_LTE",
            "n_NLTE",
            "ion_popfrac",
        ],
    )
    return lte_populations


def coulomb_loss_function(energy, electron_number_density, number_density):
    """Calculates the Coulomb loss function for a given energy,
    electron number density, and atom number density

    Parameters
    ----------
    energy : float
        electron energy
    electron_number_density : float

    number_density : float

    Returns
    -------
    float
        Coulomb loss energy
    """
    plasma_frequency = 56414.6 * np.sqrt(electron_number_density)
    zeta_electron = 2.0 * H_BAR * plasma_frequency
    electron_fraction = electron_number_density / number_density

    if energy > 14:
        assert 2 * energy > zeta_electron
        return (
            electron_fraction
            * (2 * np.pi * E_CHARGE ** 4)
            / energy
            * np.log(2 * energy / zeta_electron)
        )
    else:
        v = np.sqrt(2 * energy / M_E)
        euler_gamma = 0.577215664901532
        return (
            electron_fraction
            * (2 * np.pi * E_CHARGE ** 4)
            / energy
            * np.log(
                M_E * v ** 3 / (euler_gamma * E_CHARGE ** 2 * plasma_frequency)
            )
        )


def cross_section(
    energy, initial_electron_energy, oscillator_strength, van_regemorter_fit
):
    k = initial_electron_energy / 13.60

    return (
        (8 * np.pi)
        / np.sqrt(3)
        * (1 / k ** 2)
        * (H_ION_POTENTIAL / energy)
        * oscillator_strength
        * van_regemorter_fit
        * const.a0 ** 2
    )


def arnaud_cross_section(energy, ion_potential, A, B, C, D):
    """Arnaud and Rothenburg 1985 cross sections
    But calculated instead

    Parameters
    ----------
    energy : [type]
        [description]
    ion_potential : [type]
        [description]
    A : [type]
        [description]
    B : [type]
        [description]
    C : [type]
        [description]
    D : [type]
        [description]

    Returns
    -------
    [type]
        [description]
    """
    u = energy / ion_potential
    if u <= 1:
        return 0

    return (
        1e-14
        * (
            A * (1 - 1 / u)
            + B * (1 - 1 / u) ** 2
            + C * np.log(u)
            + D * np.log(u) / u
        )
        / (u * ion_potential ** 2)
    )


def get_arnaud_cross_section_array_shell(energy_grid, shell):
    arnaud_cross_section_array = np.array(
        [
            arnaud_cross_section(
                energy, shell.ion_potential, shell.A, shell.B, shell.C, shell.D
            )
            for energy in energy_grid
        ]
    )

    return arnaud_cross_section_array


def excitation_cross_section_vector(energy_grid, row):
    A0_squared = A0 ** 2  # Bohr radius squared in cm^2
    cross_section_excitation_vector = np.empty(energy_grid.size)

    coll_str = row.collstr
    epsilon_trans = (
        row.epsilon_trans_ev * EV2ERG
    )  # electron volt converted to erg
    epsilon_trans_ev = row.epsilon_trans_ev

    start_index = np.ceil(
        (epsilon_trans_ev - energy_grid.energy_min) / energy_grid.delta_energy
    )
    cross_section_excitation_vector[:start_index] = 0.0

    if coll_str >= 0:
        # collision strength is available, so use it
        # Li et al. 2012 equation 11
        constantfactor = (
            H_ION_POTENTIAL ** 2 / row.lower_g * coll_str * np.pi * A0_squared
        )

        cross_section_excitation_vector[start_index:] = (
            constantfactor * (energy_grid.grid[start_index:] * EV2ERG) ** -2
        )

    elif not row.forbidden:

        nu_trans = epsilon_trans / H
        g = row.upper_g / row.lower_g
        fij = (
            g
            * M_E
            * C_LIGHT ** 3
            / (8 * (E_CHARGE * nu_trans * np.pi) ** 2)
            * row.A
        )
        # permitted E1 electric dipole transitions

        g_bar = 0.2

        A = 0.28
        B = 0.15

        prefactor = 45.585750051
        # Eq 4 of Mewe 1972, possibly from Seaton 1962?
        constantfactor = (
            prefactor
            * A0_squared
            * (H_ION_POTENTIAL / epsilon_trans) ** 2
            * fij
        )

        U = energy_grid.grid[start_index:] / epsilon_trans_ev
        g_bar = A * np.log(U) + B

        cross_section_excitation_vector[start_index:] = (
            constantfactor * g_bar / U
        )
        for j, energy_ev in enumerate(energy_grid.grid):
            energy = energy_ev * EV2ERG
            if energy >= epsilon_trans:
                U = energy / epsilon_trans
                g_bar = A * np.log(U) + B
                cross_section_excitation_vector[j] = constantfactor * g_bar / U
    else:
        cross_section_excitation_vector[start_index:] = 0.0

    return cross_section_excitation_vector


def get_J(atomic_number, ionization_number, ion_potential):
    # returns an energy in eV
    # values from Opal et al. 1971 as applied by Kozma & Fransson 1992
    if ionization_number == 1:
        if atomic_number == 2:  # He I
            return 15.8
        elif atomic_number == 10:  # Ne I
            return 24.2
        elif atomic_number == 18:  # Ar I
            return 10.0

    return 0.6 * ion_potential


def get_index(indexed_energy, energy_grid):
    assert indexed_energy >= energy_grid[0]
    assert indexed_energy < (
        energy_grid[-1] + (energy_grid[1] - energy_grid[0])
    )

    for i, energy in enumerate(energy_grid):
        if energy < indexed_energy:
            index = i

    return index


def spencer_fano_matrix_add_ionization_shell(
    energy_grid, number_ion, shell, spencer_fano_matrix
):
    """contains the terms related to ionisation cross sections"""
    ion_potential = shell.ion_potential
    J = get_J(shell.atomic_number, shell.ion_number, ion_potential)

    arnaud_cross_section_array = get_arnaud_cross_section_array_shell(
        energy_grid.grid, shell
    )

    if ion_potential <= energy_grid.grid[0]:
        cross_section_start_index = 0
    else:
        cross_section_start_index = get_index(ion_potential, energy_grid.grid)

    for i, energy in enumerate(energy_grid.grid):
        # // endash ranges from en to SF_EMAX, but skip over the zero-cross section points
        j_start = (
            i if i > cross_section_start_index else cross_section_start_index
        )
        if (
            2 * energy + ion_potential
            < energy_grid.grid[-1] + energy_grid.delta_energy
        ):
            second_integral_start_index = get_index(
                2 * energy + ion_potential, energy_grid.grid
            )
        else:
            second_integral_start_index = energy_grid.size + 1

        # integral/J of 1/[1 + (epsilon - ion_potential) / J] for epsilon = en + ion_potential
        for j in range(j_start, energy_grid.size):
            # j is the matrix column index which corresponds to the piece of the
            # integral at y(E') where E' >= E and E' = envec(j)
            energy_dash = energy_grid.grid[j]
            prefactor = (
                number_ion
                * arnaud_cross_section_array[j]
                / np.arctan((energy_dash - ion_potential) / 2.0 / J)
                * energy_grid.delta_energy
            )
            assert not np.isnan(prefactor)
            assert not np.isinf(prefactor)
            # assert prefactor >= 0

            # J * atan[(epsilon - ionpot_ev) / J] is the indefinite integral of
            # 1/(1 + (epsilon - ionpot_ev)^2/ J^2) d_epsilon
            # in Kozma & Fransson 1992 equation 4

            # KF 92 limit
            epsilon_upper = (energy_dash + ion_potential) / 2
            # Li+2012 limit
            # epsilon_upper = (endash + en) / 2

            int_eps_upper = np.arctan((epsilon_upper - ion_potential) / J)

            epsilon_lower = energy_dash - energy
            int_eps_lower = np.arctan((epsilon_lower - ion_potential) / J)

            spencer_fano_matrix[i, j] += prefactor * (
                int_eps_upper - int_eps_lower
            )

            epsilon_lower = energy + ion_potential
            epsilon_upper = (energy_dash + ion_potential) / 2
            # endash ranges from 2 * en + ionpot_ev to SF_EMAX
            if j >= second_integral_start_index + 1:
                # int_eps_upper = atan((epsilon_upper - ionpot_ev) / J)
                int_eps_lower = np.arctan((epsilon_lower - ion_potential) / J)
                if epsilon_lower > epsilon_upper:
                    print(
                        j,
                        second_integral_start_index,
                        epsilon_lower,
                        epsilon_upper,
                    )
                assert epsilon_lower <= epsilon_upper

                spencer_fano_matrix[i, j] -= prefactor * (
                    int_eps_upper - int_eps_lower
                )

    return spencer_fano_matrix


def spencer_fano_matrix_add_excitation(
    energy_grid, transitions_dict, nnion, sfmatrix
):
    delta_energy = energy_grid.delta_energy
    points = energy_grid.size
    for _, row in transitions_dict.iterrows():
        nnlevel = row.lower_pop
        epsilon_trans_ev = row.epsilon_trans_ev
        if epsilon_trans_ev >= energy_grid.grid[0]:
            vec_xs_excitation_nnlevel_deltae = (
                nnlevel
                * delta_energy
                * excitation_cross_section_vector(energy_grid, row)
            )
            for i in range(points):
                stop_index = i + np.ceil(epsilon_trans_ev / delta_energy)

                if stop_index < points - 1:
                    sfmatrix[
                        i, i : stop_index - i + 1
                    ] += vec_xs_excitation_nnlevel_deltae[
                        i : stop_index - i + 1
                    ]


def solve_spencer_fano(
    energy_grid,
    source_vector,
    electron_number_density,
    number_density,
    ions,
    energy_deposition_density,
    ion_collision_data,
    lte_populations,
    atomic_levels,
    ion_populations,
):
    delta_energy = energy_grid.delta_energy
    points = energy_grid.size

    initial_energy = np.dot(energy_grid.grid, source_vector) * delta_energy

    # set up the constant vector
    # sum of source vector times dE
    # same size as energy grid
    constant_vector = np.zeros(points)
    for i in range(points):
        for j in range(i, points):
            constant_vector[i] += source_vector[j] * delta_energy

    spencer_fano_matrix = np.zeros((points, points))
    for i, energy in enumerate(energy_grid.grid):
        spencer_fano_matrix[i, i] += coulomb_loss_function(
            energy, electron_number_density, number_density
        )

    transitions_dict = {}

    for ion_info, value in ions.iteritems():
        atomic_number, ion_number = ion_info[0], ion_info[1]
        number_ion = ion_populations[(atomic_number, ion_number)]
        ion_collision_data_current = ion_collision_data.query(
            "atomic_number == @atomic_number and ion_number == @ion_number",
            inplace=False,
        )

        for index, shell in ion_collision_data_current.iterrows():
            assert shell.ion_potential >= energy_grid.grid[0]
            spencer_fano_matrix = spencer_fano_matrix_add_ionization_shell(
                energy_grid,
                number_ion,
                shell,
                spencer_fano_matrix,
            )

        # queries dataframe
        population_current_ion = lte_populations.query(
            "atomic_number==@atomic_number & ion_number==@ion_number"
        )
        population_dict = {
            x.level: x["n_NLTE"] for _, x in population_current_ion.iterrows()
        }

        ion = atomic_levels.query(
            "atomic_number == @atomic_number and ion_number == @ion_number"
        ).iloc[0]
        # Horrible syntax, probably a better way with Carsus/plasma input
        ground_level_no_j = ion.levels.iloc[0].levelname.split("[")[0]
        # Currently set to 4 after this in Andreas code
        top_gm_level = ion.levels[
            ion.levels.levelname.str.startswith(ground_level_no_j)
        ].index.max()
        transitions_dict[(atomic_number, ion_number)] = ion.transitions.query(
            "lower <= @top_gm_level", inplace=False
        ).copy()

        if not transitions_dict[(atomic_number, ion_number)].empty:
            transitions_dict[(atomic_number, ion_number)].query(
                "collstr >= 0 or forbidden == False", inplace=True
            )
            transitions_dict[(atomic_number, ion_number)].eval(
                "epsilon_trans_ev = "
                "@ion.levels.loc[upper].energy_ev.values - @ion.levels.loc[lower].energy_ev.values",
                inplace=True,
            )
            transitions_dict[(atomic_number, ion_number)].query(
                "epsilon_trans_ev >= @engrid[0]", inplace=True
            )
            transitions_dict[(atomic_number, ion_number)].eval(
                "lower_g = @ion.levels.loc[lower].g.values", inplace=True
            )
            transitions_dict[(atomic_number, ion_number)].eval(
                "upper_g = @ion.levels.loc[upper].g.values", inplace=True
            )
            transitions_dict[(atomic_number, ion_number)][
                "lower_pop"
            ] = transitions_dict[(atomic_number, ion_number)].apply(
                lambda x: population_dict.get(x.lower, 0.0), axis=1
            )

            spencer_fano_matrix_add_excitation(
                energy_grid,
                transitions_dict[(atomic_number, ion_number)],
                number_ion,
                spencer_fano_matrix,
            )

    lu_and_piv = linalg.lu_factor(spencer_fano_matrix, overwrite_a=False)
    y_vector_reference = linalg.lu_solve(lu_and_piv, constant_vector, trans=0)
    y_vector = y_vector_reference * energy_deposition_density / initial_energy

    return y_vector, transitions_dict


def setup_solution(
    energy_min,
    energy_max,
    points,
    temperature,
    plasma,
    energy_deposition_density,
):

    energy_grid = Energy_Grid(energy_min, energy_max, points)

    source_vector = np.zeros_like(energy_grid.grid)
    source_spread_points = np.ceil(points * 0.03)
    for s in range(points):
        # spread the source over some energy width
        if s < points - source_spread_points:
            source_vector[s] = 0.0
        elif s < points:
            source_vector[s] = 1.0 / (
                energy_grid.delta_energy * source_spread_points
            )

    atomic_levels = plasma.atomic_data.levels
    lte_populations = plasma.level_boltzmann_factor
    ion_collision_data = plasma.ion_collision_data
    number_density = plasma.number_density[0]
    ion_populations = plasma.ion_number_density[0]
    electron_number_density = plasma.electron_densities[
        0
    ]  # not sure if number density but should be
    ions = plasma.ionization_data

    electron_spectrum, transitions_dict = solve_spencer_fano(
        energy_grid,
        source_vector,
        electron_number_density,
        number_density,
        ions,
        energy_deposition_density,
        ion_collision_data,
        lte_populations,
        atomic_levels,
        ion_populations,
    )

    return electron_spectrum, transitions_dict