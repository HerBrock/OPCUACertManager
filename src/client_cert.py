"""
Module to create OPC UA client certificates.

These certificates are signed by the CA created in ca.py.
"""

import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from .utils import (
    load_ca_from_disk,
    save_key_and_cert_to_pem,
)


def generate_client_key(
    key_size: int = 2048,
) -> rsa.RSAPrivateKey:
    """
    Generate an RSA private key for the OPC UA client.
    """
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )


def build_client_certificate(
    client_private_key: rsa.RSAPrivateKey,
    ca_private_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    country_name: str = "ES",
    state_name: str = "Madrid",
    locality_name: str = "Madrid",
    organization_name: str = "MyCompany",
    common_name: str = "opcua-client",
    san_list: list[str] | None = None,
    validity_days: int = 365,
) -> x509.Certificate:
    """
    Build an X.509 certificate for an OPC UA client.

    The certificate is signed by the CA private key.
    """

    subject = x509.Name(
        [
            x509.NameAttribute(
                NameOID.COUNTRY_NAME,
                country_name,
            ),
            x509.NameAttribute(
                NameOID.STATE_OR_PROVINCE_NAME,
                state_name,
            ),
            x509.NameAttribute(
                NameOID.LOCALITY_NAME,
                locality_name,
            ),
            x509.NameAttribute(
                NameOID.ORGANIZATION_NAME,
                organization_name,
            ),
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                common_name,
            ),
        ]
    )

    issuer = ca_cert.subject
    now = datetime.now(timezone.utc)

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(client_private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(
            now + timedelta(days=validity_days)
        )
    )

    # The client certificate is not a CA.
    builder = builder.add_extension(
        x509.BasicConstraints(
            ca=False,
            path_length=None,
        ),
        critical=True,
    )

    # Key usage for signing and TLS key exchange.
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )

    # This certificate authenticates a client.
    builder = builder.add_extension(
        x509.ExtendedKeyUsage(
            [
                ExtendedKeyUsageOID.CLIENT_AUTH,
            ]
        ),
        critical=False,
    )

    # Optional Subject Alternative Names.
    if san_list:
        san_entries = []

        for name in san_list:
            name = name.strip()

            if name.upper().startswith("DNS:"):
                dns_name = name.split(":", 1)[1].strip()
                san_entries.append(x509.DNSName(dns_name))

            elif name.upper().startswith("IP:"):
                ip_text = name.split(":", 1)[1].strip()
                ip_address = ipaddress.ip_address(ip_text)
                san_entries.append(x509.IPAddress(ip_address))

            else:
                san_entries.append(x509.DNSName(name))

        if san_entries:
            builder = builder.add_extension(
                x509.SubjectAlternativeName(san_entries),
                critical=False,
            )

    return builder.sign(
        ca_private_key,
        hashes.SHA256(),
    )


def create_client_certificate(
    client_folder: str | Path = "certs/client",
    ca_folder: str | Path = "certs/ca",
    key_size: int = 2048,
    country_name: str = "ES",
    state_name: str = "Madrid",
    locality_name: str = "Madrid",
    organization_name: str = "MyCompany",
    common_name: str = "opcua-client",
    san_list: list[str] | None = None,
    validity_days: int = 365,
) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """
    Create and save a complete OPC UA client certificate.

    The function:
    1. Loads the CA from disk.
    2. Generates the client private key.
    3. Builds the client certificate.
    4. Saves the key and certificate to disk.

    Returns:
        A tuple containing the client private key and certificate.
    """

    ca_private_key, ca_cert = load_ca_from_disk(ca_folder)

    client_private_key = generate_client_key(key_size)

    certificate = build_client_certificate(
        client_private_key=client_private_key,
        ca_private_key=ca_private_key,
        ca_cert=ca_cert,
        country_name=country_name,
        state_name=state_name,
        locality_name=locality_name,
        organization_name=organization_name,
        common_name=common_name,
        san_list=san_list,
        validity_days=validity_days,
    )

    save_key_and_cert_to_pem(
        private_key=client_private_key,
        cert=certificate,
        folder_path=client_folder,
        key_filename="client_key.pem",
        cert_filename="client_cert.pem",
    )

    return client_private_key, certificate