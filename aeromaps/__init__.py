# Contains the principal high-level functions of AeroMAPS
from aeromaps.core.models import default_models_top_down
from aeromaps.core.process import AeroMAPSProcess
from aeromaps.conf.config import Config
import hydra
from omegaconf import DictConfig, OmegaConf
from pathlib import Path
import os

def load_config(config_path: str = "conf", config_name: str = "config.yaml") -> Config:
    script_dir = Path(__file__).parent.absolute()
    os.environ["SCRIPT_DIR"] = str(script_dir)
    
    with hydra.initialize(config_path=config_path):
        cfg = hydra.compose(config_name=config_name)
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
