"""Create OPC UA server certificates signed by a project CA."""

from __future__ import annotations

import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

ExportFormat = Literal["PEM", "DER"]
VALID_KEY_SIZES = (2048, 4096)
VALID_CERT_EXTENSIONS = (".pem", ".cer", ".crt")


def generate_server_key(key_size: int = 2048) -> rsa.RSAPrivateKey:
    """Generate an RSA private key for an OPC UA server."""
    _validate_key_size(key_size)
    return rsa.generate_private_key(public_exponent=65537, key_size=key_size)


def _validate_key_size(key_size: int) -> None:
    """Validate the supported RSA key sizes."""
    if key_size not in VALID_KEY_SIZES:
        raise ValueError(f"key_size must be one of {VALID_KEY_SIZES}; received {key_size}.")


def _validate_positive_days(validity_days: int) -> None:
    """Validate a positive certificate validity period."""
    if validity_days <= 0:
        raise ValueError("validity_days must be greater than zero.")


def _build_san_entries(san_list: list[str] | None) -> list[x509.GeneralName]:
    """Convert DNS, IP, and URI SAN strings into cryptography objects."""
    entries: list[x509.GeneralName] = []
    for raw_name in san_list or []:
        name = raw_name.strip()
        if not name:
            continue

        prefix, separator, value = name.partition(":")
        prefix = prefix.upper()
        value = value.strip() if separator else name

        if prefix == "DNS" and separator:
            entries.append(x509.DNSName(value))
        elif prefix == "IP" and separator:
            entries.append(x509.IPAddress(ipaddress.ip_address(value)))
        elif prefix == "URI" and separator:
            entries.append(x509.UniformResourceIdentifier(value))
        else:
            entries.append(x509.DNSName(name))

    return entries


def build_server_certificate(
    server_private_key: rsa.RSAPrivateKey,
    ca_private_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    country_name: str = "ES",
    state_name: str = "Madrid",
    locality_name: str = "Madrid",
    organization_name: str = "MyCompany",
    common_name: str = "opcua-server.local",
    san_list: list[str] | None = None,
    validity_days: int = 365,
) -> x509.Certificate:
    """Build an OPC UA server certificate signed by the supplied CA."""
    _validate_positive_days(validity_days)
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country_name),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state_name),
        x509.NameAttribute(NameOID.LOCALITY_NAME, locality_name),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization_name),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])

    now = datetime.now(timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(server_private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=validity_days))
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
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
    )

    san_entries = _build_san_entries(san_list)
    if san_entries:
        builder = builder.add_extension(
            x509.SubjectAlternativeName(san_entries),
            critical=False,
        )

    return builder.sign(ca_private_key, hashes.SHA256())


def load_ca_from_disk(ca_folder: str | Path) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """Load ``ca_key.pem`` and ``ca_cert.pem`` from a project folder."""
    folder = Path(ca_folder)
    key_path = folder / "ca_key.pem"
    cert_path = folder / "ca_cert.pem"
    if not key_path.is_file() or not cert_path.is_file():
        raise FileNotFoundError(f"CA files not found in {folder}")

    ca_private_key = serialization.load_pem_private_key(
        key_path.read_bytes(),
        password=None,
    )
    ca_cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
    return ca_private_key, ca_cert


def _serialize_certificate(cert: x509.Certificate, export_format: ExportFormat) -> bytes:
    """Serialize a certificate as PEM text or DER binary."""
    if export_format == "PEM":
        return cert.public_bytes(serialization.Encoding.PEM)
    if export_format == "DER":
        return cert.public_bytes(serialization.Encoding.DER)
    raise ValueError("export_format must be 'PEM' or 'DER'.")


def _write_private_key(key: rsa.RSAPrivateKey, path: Path) -> None:
    """Write a private key as unencrypted PKCS#8 PEM."""
    path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )


def _certificate_extension(export_format: ExportFormat, cert_extension: str | None) -> str:
    """Resolve and validate the certificate filename extension."""
    extension = (cert_extension or (".pem" if export_format == "PEM" else ".cer")).lower()
    if not extension.startswith("."):
        extension = f".{extension}"
    if extension not in VALID_CERT_EXTENSIONS:
        raise ValueError(f"cert_extension must be one of {VALID_CERT_EXTENSIONS}.")
    return extension


def create_server_certificate(
    server_folder: str | Path = "certs/server",
    ca_folder: str | Path = "certs/ca",
    key_size: int = 2048,
    country_name: str = "ES",
    state_name: str = "Madrid",
    locality_name: str = "Madrid",
    organization_name: str = "MyCompany",
    common_name: str = "opcua-server.local",
    san_list: list[str] | None = None,
    validity_days: int = 365,
    export_format: ExportFormat = "PEM",
    cert_extension: str | None = None,
    certificate_name: str = "server_cert",
    overwrite: bool = True,
) -> dict:
    """Create, sign, and save an OPC UA server certificate and private key.

    The private key always remains unencrypted PEM and keeps the ``_key.pem``
    suffix. Only the public certificate changes between PEM and DER formats.
    """
    try:
        _validate_key_size(key_size)
        _validate_positive_days(validity_days)
        if not certificate_name or Path(certificate_name).name != certificate_name:
            raise ValueError("certificate_name must be a simple filename without path separators.")

        ca_private_key, ca_cert = load_ca_from_disk(ca_folder)
        server_private_key = generate_server_key(key_size)
        cert = build_server_certificate(
            server_private_key,
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

        folder = Path(server_folder)
        folder.mkdir(parents=True, exist_ok=True)
        extension = _certificate_extension(export_format, cert_extension)
        cert_path = folder / f"{certificate_name}{extension}"
        key_path = folder / f"{certificate_name}_key.pem"
        if not overwrite and (cert_path.exists() or key_path.exists()):
            raise FileExistsError(f"Output file already exists: {cert_path}")

        cert_path.write_bytes(_serialize_certificate(cert, export_format))
        _write_private_key(server_private_key, key_path)
        now = datetime.now(timezone.utc)
        subject = _format_name(cert.subject)
        issuer = _format_name(cert.issuer)
        return {
            "success": True,
            "server_key_path": str(key_path),
            "server_cert_path": str(cert_path),
            "fecha_expiracion": cert.not_valid_after_utc.isoformat(),
            "sujeto": subject,
            "emisor": issuer,
            "error": None,
        }
    except Exception as error:
        return {
            "success": False,
            "server_key_path": None,
            "server_cert_path": None,
            "fecha_expiracion": None,
            "sujeto": None,
            "emisor": None,
            "error": str(error),
        }


def _format_name(name: x509.Name) -> str:
    """Return a readable subject or issuer string."""
    aliases = {
        NameOID.COUNTRY_NAME: "C",
        NameOID.STATE_OR_PROVINCE_NAME: "ST",
        NameOID.LOCALITY_NAME: "L",
        NameOID.ORGANIZATION_NAME: "O",
        NameOID.COMMON_NAME: "CN",
    }
    return ", ".join(f"{aliases.get(attribute.oid, attribute.oid._name)}={attribute.value}" for attribute in name)
