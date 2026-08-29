"""
Common utilities for certificate management.

Functions used by multiple modules (ca, server_cert, client_cert).
"""

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pathlib import Path
from typing import Tuple


def load_ca_from_disk(
    ca_folder: str | Path = "certs/ca",
    key_filename: str = "ca_key.pem",
    cert_filename: str = "ca_cert.pem",
) -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """
    Load the CA private key and certificate from disk.

    Returns (ca_private_key, ca_cert).
    """
    folder = Path(ca_folder)

    key_path = folder / key_filename
    cert_path = folder / cert_filename

    # Load private key
    with open(key_path, "rb") as f:
        ca_private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
        )
        if not isinstance(ca_private_key, rsa.RSAPrivateKey):
            raise TypeError("CA key is not an RSA key")

    # Load certificate
    with open(cert_path, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())

    return ca_private_key, ca_cert


def save_key_and_cert_to_pem(
    private_key: rsa.RSAPrivateKey,
    cert: x509.Certificate,
    folder_path: str | Path,
    key_filename: str,
    cert_filename: str,
) -> None:
    """
    Save a private key and a certificate to PEM files.

    This is generic and works for CA, server, or client.
    """
    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)

    key_path = folder / key_filename
    cert_path = folder / cert_filename

    # Save private key
    with open(key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Save certificate
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


def ensure_folder(path: str | Path) -> Path:
    """
    Create a folder if it does not exist and return its Path.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p