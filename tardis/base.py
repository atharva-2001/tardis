# functions that are important for the general usage of TARDIS


def run_tardis(
    config,
    atom_data=None,
    packet_source=None,
    simulation_callbacks=[],
    virtual_packet_logging=False,
    show_cplots=True,
    **kwargs,
):
    """
    This function is one of the core functions to run TARDIS from a given
    config object.

    It will return a model object containing

    Parameters
    ----------
    config : str or dict or tardis.io.config_reader.Configuration
        filename of configuration yaml file or dictionary or TARDIS Configuration object
    atom_data : str or tardis.atomic.AtomData
        if atom_data is a string it is interpreted as a path to a file storing
        the atomic data. Atomic data to use for this TARDIS simulation. If set to None, the
        atomic data will be loaded according to keywords set in the configuration
        [default=None]
    virtual_packet_logging : bool
        option to enable virtual packet logging
        [default=False]

    Returns
    -------
    Simulation
    """
    from tardis.io.config_reader import Configuration
    from tardis.io.atom_data.base import AtomData
    from tardis.simulation import Simulation

    if atom_data is not None:
        try:
            atom_data = AtomData.from_hdf(atom_data)
        except TypeError:
            atom_data = atom_data

    if isinstance(config, Configuration):
        tardis_config = config
    else:
        try:
            tardis_config = Configuration.from_yaml(config)
        except TypeError:
            tardis_config = Configuration.from_config_dict(config)

    if not isinstance(show_cplots, bool):
        raise TypeError("Expected bool in show_cplots argument")

    simulation = Simulation.from_config(
        tardis_config,
        packet_source=packet_source,
        atom_data=atom_data,
        virtual_packet_logging=virtual_packet_logging,
        show_cplots=show_cplots,
        **kwargs,
    )
    for cb in simulation_callbacks:
        simulation.add_callback(*cb)

    simulation.run()

    return simulation
