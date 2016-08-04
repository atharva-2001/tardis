import time
import logging
import numpy as np

from tardis.montecarlo.base import MontecarloRunner

# Adding logging support
logger = logging.getLogger(__name__)


class Simulation(object):
    def __init__(self, iterations, model, plasma, atom_data, no_of_packets,
                 no_of_virtual_packets, luminosity_nu_start,
                 luminosity_nu_end, last_no_of_packets,
                 luminosity_requested, convergence_strategy, seed,
                 spectrum_frequency, distance, nthreads):
        self.converged = False
        self.iterations = iterations
        self.iterations_executed = 0
        self.model = model
        self.plasma = plasma
        self.atom_data = atom_data
        self.no_of_packets = no_of_packets
        self.last_no_of_packets = last_no_of_packets
        self.no_of_virtual_packets = no_of_virtual_packets
        self.luminosity_nu_start = luminosity_nu_start
        self.luminosity_nu_end = luminosity_nu_end
        self.luminosity_requested = luminosity_requested
        self.nthreads = nthreads
        self.runner = MontecarloRunner(seed,
                                       spectrum_frequency,
                                       distance)
        if convergence_strategy.type in ('damped', 'specific'):
            self.convergence_strategy = convergence_strategy
        else:
            raise ValueError('Convergence strategy type is '
                             'neither damped nor specific '
                             '- input is {0}'.format(convergence_strategy.type))

    def estimate_t_inner(self, input_t_inner, luminosity_requested,
                         t_inner_update_exponent=-0.5):
        emitted_luminosity = self.runner.calculate_emitted_luminosity(
                                self.luminosity_nu_start,
                                self.luminosity_nu_end)

        luminosity_ratios = (
            (emitted_luminosity / luminosity_requested).to(1).value)

        return input_t_inner * luminosity_ratios ** t_inner_update_exponent

    @staticmethod
    def damped_converge(value, estimated_value, damping_factor):
        # FIXME: Should convergence strategy have its own class containing this
        # as a method
        return value + damping_factor * (estimated_value - value)

    def advance_state(self):
        """
        Advances the state of the model and the plasma for the next
        iteration of the simulation.

        Returns
        -------
        : None
        """
        estimated_t_rad, estimated_w = (
            self.runner.calculate_radiationfield_properties())
        estimated_t_inner = self.estimate_t_inner(
            self.model.t_inner, self.luminosity_requested)

        # calculate_next_plasma_state equivalent
        # FIXME: Should convergence strategy have its own class?
        self.model.t_rad = self.damped_converge(
            self.model.t_rad, estimated_t_rad,
            self.convergence_strategy.t_rad.damping_constant)
        self.model.w = self.damped_converge(
            self.model.w, estimated_w, self.convergence_strategy.w.damping_constant)
        self.model.t_inner = self.damped_converge(
            self.model.t_inner, estimated_t_inner,
            self.convergence_strategy.t_inner.damping_constant)

        # model.calculate_j_blues() equivalent
        # model.update_plasmas() equivalent
        # TODO: if nlte_config is not None and nlte_config.species:
        #          self.store_previous_properties()
        self.plasma.update(t_rad=self.model.t_rad, w=self.model.w)

    def run_single(self, last_run=False):
        no_of_packets = self.no_of_packets
        if last_run:
            if self.last_no_of_packets is not None:
                no_of_packets = self.last_no_of_packets

        self.runner.run(self.model, self.plasma, no_of_packets,
                        no_of_virtual_packets=self.no_of_virtual_packets,
                        nthreads=self.nthreads, last_run=last_run)

        output_energy = self.runner.output_energy
        self.j_estimator = self.runner.j_estimator
        self.nu_bar_estimator = self.runner.nu_bar_estimator
        self.last_interaction_type = self.runner.last_interaction_type
        self.last_line_interaction_shell_id = (
            self.runner.last_line_interaction_shell_id)
        if last_run:
            self.runner.legacy_update_spectrum(self.no_of_virtual_packets)

        if np.sum(output_energy < 0) == len(output_energy):
            logger.critical("No r-packet escaped through the outer boundary.")

    def run(self):
        start_time = time.time()
        while self.iterations_executed < self.iterations:
            logger.info('Starting iteration #%d', self.iterations_executed + 1)
            self.run_single()
            emitted_luminosity = self.runner.calculate_emitted_luminosity(
                self.luminosity_nu_start, self.luminosity_nu_end)
            reabsorbed_luminosity = self.runner.calculate_reabsorbed_luminosity(
                self.luminosity_nu_start, self.luminosity_nu_end)
            self.log_run_results(emitted_luminosity,
                                 reabsorbed_luminosity)
            self.iterations_executed += 1
            self.advance_state()

    def log_run_results(self, emitted_luminosity, absorbed_luminosity):
        logger.info("Luminosity emitted = {0:.5e} "
                    "Luminosity absorbed = {1:.5e} "
                    "Luminosity requested = {2:.5e}".format(
            emitted_luminosity, absorbed_luminosity,
            self.luminosity_requested))

    @classmethod
    def from_config(cls, config):
        raise NotImplementedError()
        #TODO
