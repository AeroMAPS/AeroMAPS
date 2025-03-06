import os
from pathlib import Path

# Contains the principal high-level functions of AeroMAPS
from aeromaps.core.models import default_models_top_down
from aeromaps.core.process import AeroMAPSProcess
from aeromaps.conf.config import Config
import hydra
from hydra.core.global_hydra import GlobalHydra
from hydra.core.hydra_config import HydraConfig
from omegaconf import OmegaConf
from hydra.utils import get_original_cwd


def load_config(config_path: str = "conf", config_name: str = "config.yaml") -> Config:

    # If existing Hydra state is not cleared, you may get an error like:
    if GlobalHydra.instance().is_initialized():
        GlobalHydra.instance().clear()

    # Config path provided by the user or default
    user_config_path = Path(config_path)
    # print("config_path: ", user_config_path)

    # Get the current file parent path
    current_file_parent_path = Path(__file__).parent
    # print("current_file_parent_path: ", current_file_parent_path)

    # Get current working directory
    cwd = Path(os.getcwd())
    # print("cwd: ", cwd)

    # Build the relative path to the user config file
    config_relative_path = cwd.relative_to(current_file_parent_path) / user_config_path
    # print("config_relative_path: ", config_relative_path)

    # Build the absolute path to the config file
    config_absolute_path = cwd / user_config_path
    # print("config_absolute_path: ", config_absolute_path)

    # Verify that default arguments are used,
    # then the default config path of the project is used
    # TODO: maybe choose a more exotic default value for config_path
    if config_path == "conf" and config_name == "config.yaml":
        config_absolute_path = current_file_parent_path / user_config_path
        config_relative_path = user_config_path
        # print("New config_absolute_path: ", config_absolute_path)
        # print("New config_relative_path: ", config_relative_path)

    #Initialize Hydra
    with hydra.initialize(version_base=None, config_path=str(config_relative_path)):
        cfg = hydra.compose(config_name=config_name, return_hydra_config=True)

        if not HydraConfig.initialized():
            HydraConfig.instance().set_config(cfg)

    # Get the original working directory
    original_cwd = Path(get_original_cwd())
    # print("original_cwd: ", original_cwd)

    # Rebuild all paths in the configuration to be absolute
    for key, value in cfg.items():
        if isinstance(value, str):
            cfg[key] = str(config_absolute_path / value)

    cfg = OmegaConf.create({k: v for k, v in cfg.items() if k != "hydra"})

    return OmegaConf.merge(OmegaConf.structured(Config()), cfg)

def create_process(
    cfg: Config,
    models=default_models_top_down,
    use_fleet_model=False,
    add_examples_aircraft_and_subcategory=True,
) -> AeroMAPSProcess:
    """
    Create an AeroMAPS process.
    """
    return AeroMAPSProcess(
        cfg=cfg,
        models=models,
        use_fleet_model=use_fleet_model,
        add_examples_aircraft_and_subcategory=add_examples_aircraft_and_subcategory,
    )

def another_function(cfg: Config):
    """
    Another function that uses the configuration.
    """
    # Use the configuration as needed
    print(cfg)
