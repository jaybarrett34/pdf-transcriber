import yaml
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Try local config first, then default
            local_config = Path("config/local_config.yaml")
            default_config = Path("config/default_config.yaml")

            if local_config.exists():
                config_path = str(local_config)
            else:
                config_path = str(default_config)

        with open(config_path, 'r') as f:
            self.config: Dict[str, Any] = yaml.safe_load(f)

    def get(self, key_path: str, default=None):
        """Get config value using dot notation: 'ocr.engine'"""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def __getitem__(self, key):
        return self.config[key]

    def __contains__(self, key):
        return key in self.config

# Global config instance
_config = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config

def reload_config(config_path: str = None):
    global _config
    _config = Config(config_path)
    return _config
