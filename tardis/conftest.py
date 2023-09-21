"""Configure Test Suite.

This file is used to configure the behavior of pytest when using the Astropy
test infrastructure. It needs to live inside the package in order for it to
get picked up when running the tests inside an interpreter using
packagename.test

"""

import os
from pathlib import Path

from astropy.version import version as astropy_version

# For Astropy 3.0 and later, we can use the standalone pytest plugin
if astropy_version < "3.0":
    from astropy.tests.pytest_plugins import *  # noqa

    del pytest_report_header
    ASTROPY_HEADER = True
else:
    try:
        from pytest_astropy_header.display import (
            PYTEST_HEADER_MODULES,
            TESTED_VERSIONS,
        )

        ASTROPY_HEADER = True
    except ImportError:
        ASTROPY_HEADER = False


def pytest_configure(config):
    """Configure Pytest with Astropy.

    Parameters
    ----------
    config : pytest configuration

    """
    if ASTROPY_HEADER:

        config.option.astropy_header = True

        # Customize the following lines to add/remove entries from the list of
        # packages for which version numbers are displayed when running the tests.
        PYTEST_HEADER_MODULES.pop("Pandas", None)
        PYTEST_HEADER_MODULES["scikit-image"] = "skimage"

        from . import __version__

        packagename = os.path.basename(os.path.dirname(__file__))
        TESTED_VERSIONS[packagename] = __version__

    # Create a marker to ignore the `--generate-reference` flag. A use case for this
    # marker is when there is data in the reference data repository that can't be
    # generated by TARDIS, like the Arepo snapshots.
    config.addinivalue_line(
        "markers",
        "ignore_generate: mark test to not generate new reference data",
    )


# Uncomment the last two lines in this block to treat all DeprecationWarnings as
# exceptions. For Astropy v2.0 or later, there are 2 additional keywords,
# as follow (although default should work for most cases).
# To ignore some packages that produce deprecation warnings on import
# (in addition to 'compiler', 'scipy', 'pygments', 'ipykernel', and
# 'setuptools'), add:
#     modules_to_ignore_on_import=['module_1', 'module_2']
# To ignore some specific deprecation warning messages for Python version
# MAJOR.MINOR or later, add:
#     warnings_to_ignore_by_pyver={(MAJOR, MINOR): ['Message to ignore']}
# from astropy.tests.helper import enable_deprecations_as_exceptions  # noqa
# enable_deprecations_as_exceptions()

# -------------------------------------------------------------------------
# Here the TARDIS testing stuff begins
# -------------------------------------------------------------------------

import pytest
import pandas as pd
import numpy as np
from tardis.io.util import yaml_load_file, YAMLLoader
from tardis.io.configuration.config_reader import Configuration
from tardis.simulation import Simulation

from syrupy.data import SnapshotCollection
from syrupy.extensions.single_file import SingleFileSnapshotExtension
from syrupy.types import SerializableData
from syrupy.location import PyTestLocation
from typing import Any, List, Tuple

pytest_plugins = "syrupy"


def pytest_addoption(parser):
    parser.addoption(
        "--tardis-refdata", default=None, help="Path to Tardis Reference Folder"
    )
    parser.addoption(
        "--integration-tests",
        dest="integration-tests",
        default=None,
        help="path to configuration file for integration tests",
    )
    parser.addoption(
        "--generate-reference",
        action="store_true",
        default=False,
        help="generate reference data instead of testing",
    )
    parser.addoption(
        "--less-packets",
        action="store_true",
        default=False,
        help="Run integration tests with less packets.",
    )


# Required by the `ignore_generate` marker
def pytest_collection_modifyitems(config, items):
    if config.getoption("--generate-reference"):
        skip_generate = pytest.mark.skip(reason="Skip generate reference data")
        for item in items:
            if "ignore_generate" in item.keywords:
                item.add_marker(skip_generate)
        # automatically set update snapshots to true
        config.option.update_snapshots=True
    


# -------------------------------------------------------------------------
# project specific fixtures
# -------------------------------------------------------------------------


@pytest.fixture(scope="session")
def generate_reference(request):
    option = request.config.getoption("--generate-reference")
    if option is None:
        return False
    else:
        return option


@pytest.fixture(scope="session")
def tardis_ref_path(request):
    tardis_ref_path = request.config.getoption("--tardis-refdata")
    if tardis_ref_path is None:
        pytest.skip("--tardis-refdata was not specified")
    else:
        return Path(os.path.expandvars(os.path.expanduser(tardis_ref_path)))


from tardis.tests.fixtures.atom_data import *


@pytest.yield_fixture(scope="session")
def tardis_ref_data(tardis_ref_path, generate_reference):
    if generate_reference:
        mode = "w"
    else:
        mode = "r"
    with pd.HDFStore(tardis_ref_path / "unit_test_data.h5", mode=mode) as store:
        yield store


@pytest.fixture(scope="function")
def tardis_config_verysimple():
    return yaml_load_file(
        "tardis/io/configuration/tests/data/tardis_configv1_verysimple.yml",
        YAMLLoader,
    )


@pytest.fixture(scope="function")
def tardis_config_verysimple_nlte():
    return yaml_load_file(
        "tardis/io/configuration/tests/data/tardis_configv1_nlte.yml",
        YAMLLoader,
    )


###
# HDF Fixtures
###


@pytest.fixture(scope="session")
def hdf_file_path(tmpdir_factory):
    path = tmpdir_factory.mktemp("hdf_buffer").join("test.hdf")
    return str(path)


@pytest.fixture(scope="session")
def example_model_file_dir():
    return Path("tardis/io/model/readers/tests/data")


@pytest.fixture(scope="session")
def example_configuration_dir():
    return Path("tardis/io/configuration/tests/data")


@pytest.fixture(scope="session")
def config_verysimple(example_configuration_dir):
    return Configuration.from_yaml(
        example_configuration_dir / "tardis_configv1_verysimple.yml"
    )


@pytest.fixture(scope="function")
def config_montecarlo_1e5_verysimple(example_configuration_dir):
    return Configuration.from_yaml(
        example_configuration_dir / "tardis_configv1_verysimple.yml"
    )


@pytest.fixture(scope="session")
def simulation_verysimple(config_verysimple, atomic_dataset):
    atomic_data = deepcopy(atomic_dataset)
    sim = Simulation.from_config(config_verysimple, atom_data=atomic_data)
    sim.iterate(4000)
    return sim


# -------------------------------------------------------------------------
# fixtures and plugins for syrupy/regression data testing
# -------------------------------------------------------------------------



class NumpySnapshotExtenstion(SingleFileSnapshotExtension):
    _file_extension = "npy"

    def matches(self, *, serialized_data, snapshot_data):
        try:
            if (
                np.testing.assert_allclose(
                    np.array(snapshot_data), np.array(serialized_data)
                )
                is not None
            ):
                return False
            else:
                return True

        except:
            return False

    def _read_snapshot_data_from_location(
        self, *, snapshot_location: str, snapshot_name: str, session_id: str
    ):
        # see https://github.com/tophat/syrupy/blob/f4bc8453466af2cfa75cdda1d50d67bc8c4396c3/src/syrupy/extensions/base.py#L139
        try:
            return np.load(snapshot_location).tolist()
        except OSError:
            return None

    @classmethod
    def _write_snapshot_collection(
        cls, *, snapshot_collection: SnapshotCollection
    ) -> None:
        # see https://github.com/tophat/syrupy/blob/f4bc8453466af2cfa75cdda1d50d67bc8c4396c3/src/syrupy/extensions/base.py#L161

        filepath, data = (
            snapshot_collection.location,
            next(iter(snapshot_collection)).data,
        )
        np.save(filepath, data)

    def serialize(self, data: SerializableData, **kwargs: Any) -> str:
        return data


class PandasSnapshotExtenstion(SingleFileSnapshotExtension):
    _file_extension = "hdf"

    def matches(self, *, serialized_data, snapshot_data):
        try:
            comparer = {
                pd.Series: pd.testing.assert_series_equal,
                pd.DataFrame: pd.testing.assert_frame_equal,
            }
            try:
                comp_func = comparer[type(serialized_data)]
            except KeyError:
                raise ValueError(
                    "Can only compare Series and Dataframes with PandasSnapshotExtenstion."
                )

            if comp_func(serialized_data, snapshot_data) is not None:
                return False
            else:
                return True

        except:
            return False

    def _read_snapshot_data_from_location(
        self, *, snapshot_location: str, snapshot_name: str, session_id: str
    ):
        # see https://github.com/tophat/syrupy/blob/f4bc8453466af2cfa75cdda1d50d67bc8c4396c3/src/syrupy/extensions/base.py#L139
        try:
            data = pd.read_hdf(snapshot_location)
            return data

        except OSError:
            return None

    @classmethod
    def _write_snapshot_collection(
        cls, *, snapshot_collection: SnapshotCollection
    ) -> None:
        # see https://github.com/tophat/syrupy/blob/f4bc8453466af2cfa75cdda1d50d67bc8c4396c3/src/syrupy/extensions/base.py#L161
        filepath, data = (
            snapshot_collection.location,
            next(iter(snapshot_collection)).data,
        )
        data.to_hdf(filepath, "/data")

    def serialize(self, data: SerializableData, **kwargs: Any) -> str:
        return data


def add_refdata_repo_pandas_syrupy(refpath):
    class PandasSnapshotExtenstionRefdata(PandasSnapshotExtenstion):
        @classmethod
        def dirname(cls, *, test_location: "PyTestLocation") -> str:
            return str(Path(test_location.filepath).parent.joinpath(refpath))

    return PandasSnapshotExtenstionRefdata


def add_refdata_repo_numpy_syrupy(refpath):
    class NumpySnapshotExtenstionRefdata(NumpySnapshotExtenstion):
        @classmethod
        def dirname(cls, *, test_location: "PyTestLocation") -> str:
            return str(Path(test_location.filepath).parent.joinpath(refpath))

    return NumpySnapshotExtenstionRefdata


@pytest.fixture
def snapshot_pd(snapshot, tardis_ref_path, request):
    tardis_ref_path = tardis_ref_path.joinpath("syrupy_data")
    PandasSnapshotExtenstionRefdata = add_refdata_repo_pandas_syrupy(
        tardis_ref_path
    )
    return snapshot.use_extension(PandasSnapshotExtenstionRefdata)


@pytest.fixture
def snapshot_np(snapshot, tardis_ref_path, request):
    tardis_ref_path = tardis_ref_path.joinpath("syrupy_data")
    NumpySnapshotExtenstionRefdata = add_refdata_repo_numpy_syrupy(
        tardis_ref_path
    )
    return snapshot.use_extension(NumpySnapshotExtenstionRefdata)
