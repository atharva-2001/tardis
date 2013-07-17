import logging
import time
from pandas import HDFStore
import os

# Adding logging support
logger = logging.getLogger(__name__)


def run_radial1d(radial1d_model, history_fname=None):
    if history_fname:
        if os.path.exists(history_fname):
            logger.warn('History file %s exists - it will be overwritten', history_fname)
            os.system('rm %s' % history_fname)
        history_buffer = HDFStore(history_fname)

    start_time = time.time()
    radial1d_model.simulate(update_radiation_field=False, enable_virtual=True, initialize_j_blues=True)
    if history_fname:
        radial1d_model.to_hdf5(history_buffer, path='model%03d' % radial1d_model.iterations_executed, close_h5=False)

    while radial1d_model.iterations_remaining > 0:
        logger.info('Remaining run %d', radial1d_model.iterations_remaining)
        radial1d_model.simulate(update_radiation_field=True, enable_virtual=False)

        if history_fname:
            radial1d_model.to_hdf5(history_buffer, path='model%03d' % radial1d_model.iterations_executed, close_h5=False)

    #Finished second to last loop running one more time
    logger.info('Doing last run')
    if radial1d_model.tardis_config.montecarlo.last_no_of_packets is not None:
        radial1d_model.current_no_of_packets = radial1d_model.tardis_config.montecarlo.last_no_of_packets

    radial1d_model.simulate(enable_virtual=True, update_radiation_field=False)

    if history_fname:
        radial1d_model.to_hdf5(history_buffer, path='model%03d' % radial1d_model.iterations_executed)



    logger.info("Finished in %d iterations and took %.2f s", radial1d_model.iterations_executed, time.time()-start_time)










