"""
Certificate export utilities for OPC UA Certificate Manager.

This module provides functions to export certificates in different formats:
- PEM (Privacy Enhanced Mail) - Base64 encoded text
- DER (Distinguished Encoding Rules) - Binary format

Supported file extensions: .pem, .cer, .crt
"""

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pathlib import Path
from typing import Literal, Union


ExportFormat = Literal["PEM", "DER"]


def export_certificate(
    cert: x509.Certificate,
    output_path: str | Path,
    export_format: ExportFormat = "PEM",
) -> str:
    """
    Export a certificate to file in specified format.
    
    Args:
        cert: X.509 certificate to export.
        output_path: Output file path (extension will be adjusted if needed).
        export_format: Export format ("PEM" or "DER").
    
    Returns:
        Path to the exported file.
    
    Raises:
        ValueError: If export_format is invalid.
    """
    output_path = Path(output_path)
    
    # Determine file extension based on format
    if export_format == "PEM":
        # PEM format - text-based
        data = cert.public_bytes(serialization.Encoding.PEM)
        # Ensure correct extension for PEM
        if output_path.suffix.lower() not in [".pem", ".cer", ".crt"]:
            output_path = output_path.with_suffix(".pem")
    
    elif export_format == "DER":
        # DER format - binary
        data = cert.public_bytes(serialization.Encoding.DER)
        # Ensure correct extension for DER
        if output_path.suffix.lower() not in [".der", ".cer", ".crt"]:
            output_path = output_path.with_suffix(".cer")
    
    else:
        raise ValueError(f"Invalid export format: {export_format}. Use 'PEM' or 'DER'.")
    
    # Write to file
    with open(output_path, "wb") as f:
        f.write(data)
    
    return str(output_path)


def export_private_key(
    private_key: rsa.RSAPrivateKey,
    output_path: str | Path,
    export_format: ExportFormat = "PEM",
) -> str:
    """
    Export a private key to file in specified format.
    
    Args:
        private_key: RSA private key to export.
        output_path: Output file path.
        export_format: Export format ("PEM" or "DER").
    
    Returns:
        Path to the exported file.
    
    Raises:
        ValueError: If export_format is invalid.
    """
    output_path = Path(output_path)
    
    if export_format == "PEM":
        data = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=None,  # No password protection
        )
        if output_path.suffix.lower() != ".pem":
            output_path = output_path.with_suffix(".pem")
    
    elif export_format == "DER":
        data = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=None,
        )
        if output_path.suffix.lower() != ".der":
            output_path = output_path.with_suffix(".der")
    
    else:
        raise ValueError(f"Invalid export format: {export_format}. Use 'PEM' or 'DER'.")
    
    # Write to file
    with open(output_path, "wb") as f:
        f.write(data)
    
    return str(output_path)


def export_cert_and_key(
    cert: x509.Certificate,
    private_key: rsa.RSAPrivateKey,
    base_path: str | Path,
    export_format: ExportFormat = "PEM",
    cert_extension: str = ".pem",
) -> dict[str, str]:
    """
    Export both certificate and private key to files.
    
    Args:
        cert: X.509 certificate to export.
        private_key: RSA private key to export.
        base_path: Base path for output files (without extension).
        export_format: Export format for both files ("PEM" or "DER").
        cert_extension: Extension for certificate file (e.g., ".pem", ".cer", ".crt").
    
    Returns:
        Dictionary with keys:
        - "cert_path": Path to exported certificate.
        - "key_path": Path to exported private key.
    """
    base_path = Path(base_path)
    
    # Export certificate
    cert_path = base_path.with_suffix(cert_extension)
    export_certificate(cert, cert_path, export_format)
    
    # Export private key (always .pem for security, even if cert is DER)
    key_path = base_path.with_name(f"{base_path.stem}_key.pem")
    export_private_key(private_key, key_path, "PEM")  # Keys always PEM
    
    return {
        "cert_path": str(cert_path),
        "key_path": str(key_path),
    }


def convert_certificate(
    input_path: str | Path,
    output_path: str | Path,
    output_format: ExportFormat,
) -> str:
    """
    Convert a certificate from one format to another.
    
    Args:
        input_path: Input certificate file path.
        output_path: Output certificate file path.
        output_format: Desired output format ("PEM" or "DER").
    
    Returns:
        Path to the converted certificate.
    
    Raises:
        FileNotFoundError: If input file doesn't exist.
        ValueError: If input format cannot be determined.
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Certificate file not found: {input_path}")
    
    # Load certificate (auto-detect format)
    with open(input_path, "rb") as f:
        cert_data = f.read()
    
    try:
        # Try PEM first
        cert = x509.load_pem_x509_certificate(cert_data)
    except Exception:
        try:
            # Try DER
            cert = x509.load_der_x509_certificate(cert_data)
        except Exception:
            raise ValueError(f"Cannot load certificate: {input_path}")
    
    # Export in requested format
    return export_certificate(cert, output_path, output_format)


def get_format_from_extension(extension: str) -> ExportFormat:
    """
    Determine export format from file extension.
    
    Args:
        extension: File extension (e.g., ".pem", ".cer", ".der").
    
    Returns:
        ExportFormat ("PEM" or "DER").
    """
    ext = extension.lower()
    
    if ext in [".pem"]:
        return "PEM"
    elif ext in [".der"]:
        return "DER"
    elif ext in [".cer", ".crt"]:
        # .cer and .crt can be either PEM or DER
        # Default to PEM for compatibility
        return "PEM"
    else:
        # Default to PEM
        return "PEM"


def get_valid_extensions() -> list[str]:
    """
    Get list of valid certificate file extensions.
    
    Returns:
        List of valid extensions.
    """
    return [".pem", ".cer", ".crt", ".der"]