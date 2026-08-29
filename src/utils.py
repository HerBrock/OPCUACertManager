"""
Módulo de utilidades comunes para la gestión de certificados.

Aquí van funciones que usan varios módulos (ca, server_cert, client_cert)
para evitar código duplicado.
"""

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pathlib import Path
from typing import Tuple


def cargar_ca_desde_disk(
    ruta_carpeta_ca: str | Path = "certs/ca",
    nombre_clave: str = "ca_key.pem",
    nombre_cert: str = "ca_cert.pem",
) -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """
    Carga la clave privada y el certificado de la CA desde disco.

    Devuelve (ca_private_key, ca_cert).
    """
    carpeta = Path(ruta_carpeta_ca)

    ruta_clave = carpeta / nombre_clave
    ruta_cert = carpeta / nombre_cert

    # Cargar clave privada
    with open(ruta_clave, "rb") as f:
        ca_private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
        )
        if not isinstance(ca_private_key, rsa.RSAPrivateKey):
            raise TypeError("La clave de la CA no es RSA")

    # Cargar certificado
    with open(ruta_cert, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())

    return ca_private_key, ca_cert


def guardar_clave_y_certificado_en_pem(
    private_key: rsa.RSAPrivateKey,
    cert: x509.Certificate,
    ruta_carpeta: str | Path,
    nombre_clave: str,
    nombre_cert: str,
) -> None:
    """
    Guarda una clave privada y un certificado en archivos PEM.

    Esta función es genérica y sirve para CA, servidor o cliente.
    """
    carpeta = Path(ruta_carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)

    ruta_clave = carpeta / nombre_clave
    ruta_cert = carpeta / nombre_cert

    # Guardar clave privada
    with open(ruta_clave, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Guardar certificado
    with open(ruta_cert, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


def asegurar_carpeta(ruta: str | Path) -> Path:
    """
    Crea una carpeta si no existe y devuelve su Path.

    Útil para asegurar que las carpetas de certificados existen.
    """
    p = Path(ruta)
    p.mkdir(parents=True, exist_ok=True)
    return p