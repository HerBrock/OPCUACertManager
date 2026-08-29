"""
Módulo para cargar y guardar la configuración de la aplicación (config.json).
"""

import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "pais": "ES",
    "estado": "Madrid",
    "localidad": "Madrid",
    "organizacion": "MiEmpresa",
    "nombre_comun_ca": "MiCA OPC UA",
    "nombre_comun_servidor": "servidor-opcua.local",
    "nombre_comun_cliente": "cliente1",
    "dias_valido_ca": 3650,
    "dias_valido_servidor": 365,
    "dias_valido_cliente": 365,
    "tamano_clave_ca": 2048,
    "tamano_clave_servidor": 2048,
    "tamano_clave_cliente": 2048,
}


def obtener_ruta_config() -> Path:
    """
    Devuelve la ruta esperada para config.json (en la raíz del proyecto).
    """
    # Asumimos que config.json está en la raíz, al mismo nivel que la carpeta src
    # Desde src/config.py, la raíz es el padre del padre
    return Path(__file__).resolve().parent.parent / "config.json"


def cargar_config() -> dict[str, Any]:
    """
    Carga la configuración desde config.json.
    Si no existe o hay error, devuelve una configuración por defecto.
    """
    ruta = obtener_ruta_config()
    if not ruta.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return DEFAULT_CONFIG.copy()

        # Fusionar con defaults por si falta alguna clave
        config = DEFAULT_CONFIG.copy()
        config.update(data)
        return config
    except Exception:
        # Si hay cualquier error, usamos defaults
        return DEFAULT_CONFIG.copy()


def guardar_config(config: dict[str, Any]) -> None:
    """
    Guarda la configuración en config.json.
    """
    ruta = obtener_ruta_config()
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)