"""
Module to load and save application configuration (config.json).
"""

import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "country": "ES",
    "state": "Madrid",
    "locality": "Madrid",
    "organization": "MiEmpresa",
    "common_name_ca": "MiCA OPC UA",
    "common_name_server": "servidor-opcua.local",
    "common_name_client": "client1",
    "validity_days_ca": 3650,
    "validity_days_server": 365,
    "validity_days_client": 365,
    "key_size_ca": 2048,
    "key_size_server": 2048,
    "key_size_client": 2048,
}


def get_config_path() -> Path:
    """
    Return the expected path for config.json (in the project root).
    """
    # Assuming config.json is in the root, at the same level as the src folder
    return Path(__file__).resolve().parent.parent / "config.json"


def load_config() -> dict[str, Any]:
    """
    Load configuration from config.json.
    If it does not exist or there is an error, return default configuration.
    """
    path = get_config_path()
    if not path.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return DEFAULT_CONFIG.copy()

        # Merge with defaults in case some keys are missing
        config = DEFAULT_CONFIG.copy()
        config.update(data)
        return config
    except Exception:
        # If any error occurs, use defaults
        return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """
    Save configuration to config.json.
    """
    path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)