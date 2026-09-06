"""
Configuration management utilities.

This module handles global application configuration (config.json).
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
    Get the path to the global config.json file.
    
    Returns:
        Path to config.json in the application root.
    """
    return Path(__file__).resolve().parent.parent.parent / "config.json"


def load_config() -> dict[str, Any]:
    """
    Load global configuration from config.json.
    
    If the file doesn't exist or has errors, return default configuration.
    
    Returns:
        Dictionary with global configuration.
    """
    config_path = get_config_path()
    
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            return DEFAULT_CONFIG.copy()
        
        # Merge with defaults
        config = DEFAULT_CONFIG.copy()
        config.update(data)
        return config
    
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """
    Save global configuration to config.json.
    
    Parameters:
        config: Dictionary with configuration to save.
    """
    config_path = get_config_path()
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)