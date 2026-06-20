import logging
import logging.config
from pathlib import Path

import yaml


def setup_logging(env: str = "development") -> None:
    """
    Load logging configuration from an YAML file.
    Uses JSON logs in production, console logs otherwise.
    """
    if env == "testing":
        return

    config_path = Path(__file__).resolve().parent / "log" / "config.yaml"

    with config_path.open(mode="r") as f:
        config = yaml.safe_load(f)

    logging.config.dictConfig(config)

    logging.getLogger(__name__).info(f"Logging configured for {env} mode")
