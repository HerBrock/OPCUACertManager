"""Create OPC UA client certificates signed by a project CA."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID

from src.core.server_cert import (
    VALID_CERT_EXTENSIONS,
    _build_san_entries,
    _certificate_extension,
    _format_name,
    _serialize_certificate,
    _validate_key_size,
    _validate_positive_days,
    _write_private_key,
    build_server_certificate,
    generate_server_key,
    load_ca_from_disk,
)

ExportFormat = Literal["PEM", "DER"]


def generate_client_key(key_size: int = 2048) -> rsa.RSAPrivateKey:
    """Generate an RSA private key for an OPC UA client."""
    _validate_key_size(key_size)
    return rsa.generate_private_key(public_exponent=65537, key_size=key_size)


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
    """Build an OPC UA client certificate signed by the supplied CA."""
    _validate_positive_days(validity_days)
    subject = x509.Name([
        x509.NameAttribute(x509.NameOID.COUNTRY_NAME, country_name),
        x509.NameAttribute(x509.NameOID.STATE_OR_PROVINCE_NAME, state_name),
        x509.NameAttribute(x509.NameOID.LOCALITY_NAME, locality_name),
        x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, organization_name),
        x509.NameAttribute(x509.NameOID.COMMON_NAME, common_name),
    ])
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(client_private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + __import__("datetime").timedelta(days=validity_days))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
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
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False,
        )
    )
    san_entries = _build_san_entries(san_list)
    if san_entries:
        builder = builder.add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
    return builder.sign(ca_private_key, __import__("cryptography.hazmat.primitives.hashes", fromlist=["hashes"]).SHA256())


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
    export_format: ExportFormat = "PEM",
    cert_extension: str | None = None,
    certificate_name: str = "client_cert",
    overwrite: bool = True,
) -> dict:
    """Create, sign, and save an OPC UA client certificate and private key."""
    try:
        _validate_key_size(key_size)
        _validate_positive_days(validity_days)
        if not certificate_name or Path(certificate_name).name != certificate_name:
            raise ValueError("certificate_name must be a simple filename without path separators.")

        ca_private_key, ca_cert = load_ca_from_disk(ca_folder)
        client_private_key = generate_client_key(key_size)
        cert = build_client_certificate(
            client_private_key,
            ca_private_key,
            ca_cert,
            country_name,
            state_name,
            locality_name,
            organization_name,
            common_name,
            san_list,
            validity_days,
        )

        folder = Path(client_folder)
        folder.mkdir(parents=True, exist_ok=True)
        extension = _certificate_extension(export_format, cert_extension)
        cert_path = folder / f"{certificate_name}{extension}"
        key_path = folder / f"{certificate_name}_key.pem"
        if not overwrite and (cert_path.exists() or key_path.exists()):
            raise FileExistsError(f"Output file already exists: {cert_path}")

        cert_path.write_bytes(_serialize_certificate(cert, export_format))
        _write_private_key(client_private_key, key_path)
        return {
            "success": True,
            "client_key_path": str(key_path),
            "client_cert_path": str(cert_path),
            "fecha_expiracion": cert.not_valid_after_utc.isoformat(),
            "sujeto": _format_name(cert.subject),
            "emisor": _format_name(cert.issuer),
            "error": None,
        }
    except Exception as error:
        return {
            "success": False,
            "client_key_path": None,
            "client_cert_path": None,
            "fecha_expiracion": None,
            "sujeto": None,
            "emisor": None,
            "error": str(error),
        }
