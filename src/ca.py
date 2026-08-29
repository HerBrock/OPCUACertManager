"""
Module to create a custom CA (Certificate Authority).

This CA will be used later to sign OPC UA server and client certificates.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from .utils import save_key_and_cert_to_pem


def generate_ca_key(key_size: int = 2048) -> rsa.RSAPrivateKey:
    """
    Generate an RSA private key for the CA.
    """
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )


def build_ca_certificate(
    private_key: rsa.RSAPrivateKey,
    country_name: str = "ES",
    state_name: str = "Madrid",
    locality_name: str = "Madrid",
    organization_name: str = "MiEmpresa",
    common_name: str = "My OPC UA CA",
    validity_days: int = 3650,
) -> x509.Certificate:
    """
    Build a self-signed X.509 certificate for the CA.
    """
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, country_name),
            x509.NameAttribute(
                NameOID.STATE_OR_PROVINCE_NAME,
                state_name,
            ),
            x509.NameAttribute(NameOID.LOCALITY_NAME, locality_name),
            x509.NameAttribute(
                NameOID.ORGANIZATION_NAME,
                organization_name,
            ),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )

    # A root CA is self-signed.
    issuer = subject

    now = datetime.now(timezone.utc)

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=validity_days))
    )

    # This certificate is allowed to act as a CA.
    builder = builder.add_extension(
        x509.BasicConstraints(
            ca=True,
            path_length=None,
        ),
        critical=True,
    )

    # This key can sign certificates and certificate revocation lists.
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=True,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )

    return builder.sign(
        private_key,
        hashes.SHA256(),
    )


def create_ca(
    ca_folder: str | Path = "certs/ca",
    key_size: int = 2048,
    country_name: str = "ES",
    state_name: str = "Madrid",
    locality_name: str = "Madrid",
    organization_name: str = "MiEmpresa",
    common_name: str = "My OPC UA CA",
    validity_days: int = 3650,
) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """
    Create and save a complete Certificate Authority.

    The function:
    1. Generates the CA private key.
    2. Builds the self-signed CA certificate.
    3. Saves both files to disk.

    Returns:
        A tuple containing the private key and the certificate.
    """
    private_key = generate_ca_key(key_size)

    certificate = build_ca_certificate(
        private_key=private_key,
        country_name=country_name,
        state_name=state_name,
        locality_name=locality_name,
        organization_name=organization_name,
        common_name=common_name,
        validity_days=validity_days,
    )

    save_key_and_cert_to_pem(
        private_key=private_key,
        cert=certificate,
        folder_path=ca_folder,
        key_filename="ca_key.pem",
        cert_filename="ca_cert.pem",
    )

    return private_key, certificate