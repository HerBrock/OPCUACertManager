"""
Module to create OPC UA server certificates.

These certificates will be signed by the CA created in ca.py.

Phase 3.1 enhancement: create_server_certificate() now returns detailed certificate information.
"""

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional
import ipaddress


def generate_server_key(key_size: int = 2048) -> rsa.RSAPrivateKey:
    """
    Generate an RSA private key for the OPC UA server.
    
    Args:
        key_size: RSA key size in bits (2048 or 4096).
        
    Returns:
        RSA private key object.
    """
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )


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
    """
    Build an X.509 certificate for an OPC UA server, signed by the CA.
    
    Args:
        server_private_key: Server private key.
        ca_private_key: CA private key for signing.
        ca_cert: CA certificate.
        country_name: Country code.
        state_name: State/province name.
        locality_name: Locality/city name.
        organization_name: Organization name.
        common_name: Common Name (CN) / hostname.
        san_list: List of Subject Alternative Names.
        validity_days: Certificate validity in days.
        
    Returns:
        Server certificate signed by CA.
    """
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country_name),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state_name),
        x509.NameAttribute(NameOID.LOCALITY_NAME, locality_name),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization_name),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])

    issuer = ca_cert.subject

    now = datetime.now(timezone.utc)
    not_valid_before = now
    not_valid_after = now + timedelta(days=validity_days)

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(server_private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before)
        .not_valid_after(not_valid_after)
    )

    # Basic Constraints: NOT a CA
    builder = builder.add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True,
    )

    # Key Usage
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

    # Extended Key Usage: SERVER_AUTH
    builder = builder.add_extension(
        x509.ExtendedKeyUsage([
            ExtendedKeyUsageOID.SERVER_AUTH,
        ]),
        critical=False,
    )

    # Subject Alternative Name (SAN)
    if san_list:
        san_entries = []
        for name in san_list:
            name = name.strip()
            if name.upper().startswith("DNS:"):
                dns_name = name.split(":", 1)[1].strip()
                san_entries.append(x509.DNSName(dns_name))
            elif name.upper().startswith("IP:"):
                ip_str = name.split(":", 1)[1].strip()
                ip_obj = ipaddress.ip_address(ip_str)
                san_entries.append(x509.IPAddress(ip_obj))
            else:
                san_entries.append(x509.DNSName(name))

        if san_entries:
            builder = builder.add_extension(
                x509.SubjectAlternativeName(san_entries),
                critical=False,
            )

    cert = builder.sign(ca_private_key, hashes.SHA256())
    return cert


def load_ca_from_disk(ca_folder: str | Path) -> tuple:
    """
    Load CA private key and certificate from disk.
    
    Args:
        ca_folder: Folder path containing ca_key.pem and ca_cert.pem.
        
    Returns:
        Tuple of (ca_private_key, ca_cert).
        
    Raises:
        FileNotFoundError: If CA files don't exist.
    """
    from cryptography.hazmat.primitives import serialization
    
    ca_folder = Path(ca_folder)
    
    key_path = ca_folder / "ca_key.pem"
    cert_path = ca_folder / "ca_cert.pem"
    
    if not key_path.exists() or not cert_path.exists():
        raise FileNotFoundError(f"CA files not found in {ca_folder}")
    
    with open(key_path, "rb") as f:
        ca_private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
        )
    
    with open(cert_path, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())
    
    return ca_private_key, ca_cert


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
) -> dict:
    """
    High-level function that:
    1. Loads the CA from disk.
    2. Generates the server key.
    3. Builds the server certificate signed by the CA.
    4. Saves key and certificate to disk.

    Phase 3.1 enhancement: Returns detailed certificate information.

    Args:
        server_folder: Folder to save server certificate files.
        ca_folder: Folder containing CA files.
        key_size: RSA key size in bits.
        country_name: Country code.
        state_name: State/province name.
        locality_name: Locality/city name.
        organization_name: Organization name.
        common_name: Common Name (CN).
        san_list: List of SANs.
        validity_days: Certificate validity in days.

    Returns:
        Dictionary containing:
        - "success": True if creation was successful.
        - "server_key_path": Path to the private key file.
        - "server_cert_path": Path to the certificate file.
        - "fecha_expiracion": Expiration date (ISO format).
        - "sujeto": Full subject string.
        - "emisor": Full issuer string (the CA that signed it).
        - "error": Error message if creation failed (None otherwise).
    """
    try:
        ca_private_key, ca_cert = load_ca_from_disk(ca_folder)

        server_private_key = generate_server_key(key_size)

        cert = build_server_certificate(
            server_private_key=server_private_key,
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

        # Save files
        folder_path = Path(server_folder)
        folder_path.mkdir(parents=True, exist_ok=True)
        
        key_path = folder_path / "server_key.pem"
        cert_path = folder_path / "server_cert.pem"
        
        with open(key_path, "wb") as f:
            f.write(server_private_key.private_bytes(
                encoding=3,  # PEM format
                format=8,    # Private PKCS#8
                encryption_algorithm=None,
            ))
        
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(3))  # PEM format

        # Calculate expiration date
        fecha_expiracion = (datetime.now(timezone.utc) + timedelta(days=validity_days)).isoformat()

        # Build subject string
        sujeto = f"C={country_name}, ST={state_name}, L={locality_name}, O={organization_name}, CN={common_name}"

        # Build issuer string (from CA)
        ca_subject = ca_cert.subject
        emisor_parts = []
        for attr in ca_subject:
            oid_name = attr.oid._name
            emisor_parts.append(f"{oid_name.upper()}={attr.value}")
        emisor = ", ".join(emisor_parts)

        return {
            "success": True,
            "server_key_path": str(key_path),
            "server_cert_path": str(cert_path),
            "fecha_expiracion": fecha_expiracion,
            "sujeto": sujeto,
            "emisor": emisor,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "server_key_path": None,
            "server_cert_path": None,
            "fecha_expiracion": None,
            "sujeto": None,
            "emisor": None,
            "error": str(e),
        }