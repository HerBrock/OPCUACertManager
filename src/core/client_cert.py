"""
Module to create OPC UA client certificates.

These certificates will be signed by the CA created in ca.py.

Phase 3.1 enhancement: create_client_certificate() now returns detailed certificate information.
"""

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta, timezone
from pathlib import Path
import ipaddress


def generate_client_key(key_size: int = 2048) -> rsa.RSAPrivateKey:
    """
    Generate an RSA private key for the OPC UA client.
    
    Args:
        key_size: RSA key size in bits (2048 or 4096).
        
    Returns:
        RSA private key object.
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
    Build an X.509 certificate for an OPC UA client, signed by the CA.
    
    Args:
        client_private_key: Client private key.
        ca_private_key: CA private key for signing.
        ca_cert: CA certificate.
        country_name: Country code.
        state_name: State/province name.
        locality_name: Locality/city name.
        organization_name: Organization name.
        common_name: Common Name (CN) / client identifier.
        san_list: List of Subject Alternative Names.
        validity_days: Certificate validity in days.
        
    Returns:
        Client certificate signed by CA.
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
        .public_key(client_private_key.public_key())
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

    # Extended Key Usage: CLIENT_AUTH
    builder = builder.add_extension(
        x509.ExtendedKeyUsage([
            ExtendedKeyUsageOID.CLIENT_AUTH,
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
) -> dict:
    """
    High-level function that:
    1. Loads the CA from disk.
    2. Generates the client key.
    3. Builds the client certificate signed by the CA.
    4. Saves key and certificate to disk.

    Phase 3.1 enhancement: Returns detailed certificate information.

    Args:
        client_folder: Folder to save client certificate files.
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
        - "client_key_path": Path to the private key file.
        - "client_cert_path": Path to the certificate file.
        - "fecha_expiracion": Expiration date (ISO format).
        - "sujeto": Full subject string.
        - "emisor": Full issuer string (the CA that signed it).
        - "error": Error message if creation failed (None otherwise).
    """
    try:
        from server_cert import load_ca_from_disk
        
        ca_private_key, ca_cert = load_ca_from_disk(ca_folder)

        client_private_key = generate_client_key(key_size)

        cert = build_client_certificate(
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

        # Save files
        folder_path = Path(client_folder)
        folder_path.mkdir(parents=True, exist_ok=True)
        
        key_path = folder_path / "client_key.pem"
        cert_path = folder_path / "client_cert.pem"
        
        with open(key_path, "wb") as f:
            f.write(client_private_key.private_bytes(
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
            "client_key_path": str(key_path),
            "client_cert_path": str(cert_path),
            "fecha_expiracion": fecha_expiracion,
            "sujeto": sujeto,
            "emisor": emisor,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "client_key_path": None,
            "client_cert_path": None,
            "fecha_expiracion": None,
            "sujeto": None,
            "emisor": None,
            "error": str(e),
        }