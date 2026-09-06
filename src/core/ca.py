"""
Certificate Authority generation module.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_ca_key(key_size: int = 2048) -> rsa.RSAPrivateKey:
    """
    Generate an RSA private key for the Certificate Authority.

    Args:
        key_size: RSA key size in bits. Supported values are 2048 and 4096.

    Returns:
        Generated RSA private key.

    Raises:
        ValueError: If the key size is not supported.
    """
    if key_size not in (2048, 4096):
        raise ValueError("Key size must be 2048 or 4096 bits.")

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

    Args:
        private_key: Private RSA key used to sign the certificate.
        country_name: Two-letter country code.
        state_name: State or province.
        locality_name: City or locality.
        organization_name: Organization name.
        common_name: CA common name.
        validity_days: Certificate validity period in days.

    Returns:
        Self-signed CA certificate.
    """
    if validity_days <= 0:
        raise ValueError("Validity days must be greater than zero.")

    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, country_name),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state_name),
            x509.NameAttribute(NameOID.LOCALITY_NAME, locality_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization_name),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )

    now = datetime.now(timezone.utc)

    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=validity_days))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .add_extension(
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
        .sign(private_key, hashes.SHA256())
    )


def create_ca(
    ca_folder: str | Path,
    key_size: int = 2048,
    country_name: str = "ES",
    state_name: str = "Madrid",
    locality_name: str = "Madrid",
    organization_name: str = "MiEmpresa",
    common_name: str = "My OPC UA CA",
    validity_days: int = 3650,
) -> dict[str, str | bool | None]:
    """
    Create and save a self-signed Certificate Authority.

    Args:
        ca_folder: Destination folder for CA files.
        key_size: RSA key size.
        country_name: Country code.
        state_name: State or province.
        locality_name: City or locality.
        organization_name: Organization name.
        common_name: CA common name.
        validity_days: Validity period in days.

    Returns:
        Dictionary containing the operation result and certificate metadata.
    """
    try:
        folder_path = Path(ca_folder).resolve()
        folder_path.mkdir(parents=True, exist_ok=True)

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

        key_path = folder_path / "ca_key.pem"
        cert_path = folder_path / "ca_cert.pem"

        # Correct cryptography serialization API.
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        certificate_bytes = certificate.public_bytes(
            encoding=serialization.Encoding.PEM,
        )

        key_path.write_bytes(private_key_bytes)
        cert_path.write_bytes(certificate_bytes)

        subject = (
            f"C={country_name}, "
            f"ST={state_name}, "
            f"L={locality_name}, "
            f"O={organization_name}, "
            f"CN={common_name}"
        )

        expiration = certificate.not_valid_after_utc.isoformat()

        return {
            "success": True,
            "ca_key_path": str(key_path),
            "ca_cert_path": str(cert_path),
            "fecha_expiracion": expiration,
            "sujeto": subject,
            "emisor": subject,
            "error": None,
        }

    except Exception as error:
        return {
            "success": False,
            "ca_key_path": None,
            "ca_cert_path": None,
            "fecha_expiracion": None,
            "sujeto": None,
            "emisor": None,
            "error": str(error),
        }