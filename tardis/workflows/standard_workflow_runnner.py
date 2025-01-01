import os
# import sys
# print(f"Working Directory: {os.getcwd()}")
# print(f"PYTHONPATH: {sys.path}")
# print(f"Environment: {dict(os.environ)}")
import time
# time.sleep(10)

from tardis.io.configuration.config_reader import Configuration
from tardis.workflows.standard_tardis_workflow import StandardTARDISWorkflow


yaml_file_path = '/Users/atharva/workspace/code/tardis-main/tardis/docs/tardis_example.yml'
print(f"Current working directory: {os.getcwd()}")
print(f"About to load YAML config from: {yaml_file_path}")  # If yaml_file_path exists


# Create configuration from YAML file
config = Configuration.from_yaml(
    yaml_file_path
)

# Set debug configuration
config.debug = {}
config.debug.log_level = "WARNING"
config.debug.specific_log_level = "WARNING"

# Initialize and run workflow
workflow = StandardTARDISWorkflow(
    config,
    show_convergence_plots=False,
    show_progress_bars=False,
    convergence_plots_kwargs={"export_convergence_plots": True}
)
workflow.run()