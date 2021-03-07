from tardis import run_tardis
from tardis.io.atom_data.util import download_atom_data

# import logging

# requests_logger = logging.getLogger("tardis")
# requests_logger.setLevel(logging.ERROR)

download_atom_data("kurucz_cd23_chianti_H_He")

print(
    "verbose is 0___________________________________________________________________________________________________________________________"
)
sim = run_tardis("tardis_example.yml", verbose=0)

print(
    "verbose is 1___________________________________________________________________________________________________________________________"
)
sim = run_tardis("tardis_example.yml", verbose=1)

print(
    "verbose is 2___________________________________________________________________________________________________________________________"
)
sim = run_tardis("tardis_example.yml", verbose=2)