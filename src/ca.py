"""
Módulo para crear una CA (Certificate Authority) propia.

Esta CA se usará después para firmar certificados de servidor y cliente OPC UA.
"""

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Tuple

from .utils import guardar_clave_y_certificado_en_pem


def generar_clave_ca(tamano_clave: int = 2048) -> rsa.RSAPrivateKey:
    """
    Genera una clave privada RSA para la CA.
    """
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=tamano_clave,
    )


def construir_certificado_ca(
    private_key: rsa.RSAPrivateKey,
    nombre_pais: str = "ES",
    nombre_estado: str = "Madrid",
    nombre_localidad: str = "Madrid",
    nombre_organizacion: str = "MiEmpresa",
    nombre_comun: str = "MiCA OPC UA",
    dias_valido: int = 3650,
) -> x509.Certificate:
    """
    Construye un certificado X.509 para la CA.
    """
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, nombre_pais),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, nombre_estado),
        x509.NameAttribute(NameOID.LOCALITY_NAME, nombre_localidad),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, nombre_organizacion),
        x509.NameAttribute(NameOID.COMMON_NAME, nombre_comun),
    ])

    issuer = subject  # autofirmado

    ahora = datetime.now(timezone.utc)
    not_valid_before = ahora
    not_valid_after = ahora + timedelta(days=dias_valido)

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before)
        .not_valid_after(not_valid_after)
    )

    # Basic Constraints: es una CA
    builder = builder.add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    )

    # Key Usage: puede firmar certificados y CRL
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

    cert = builder.sign(private_key, hashes.SHA256())
    return cert


def crear_ca(
    ruta_carpeta_ca: str | Path = "certs/ca",
    tamano_clave: int = 2048,
    nombre_pais: str = "ES",
    nombre_estado: str = "Madrid",
    nombre_localidad: str = "Madrid",
    nombre_organizacion: str = "MiEmpresa",
    nombre_comun: str = "MiCA OPC UA",
    dias_valido: int = 3650,
) -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """
    Función de alto nivel que:
    1. Genera la clave de la CA.
    2. Construye el certificado de la CA.
    3. Guarda ambos en disco.

    Devuelve la clave y el certificado por si se quieren usar en memoria.
    """
    private_key = generar_clave_ca(tamano_clave)
    cert = construir_certificado_ca(
        private_key,
        nombre_pais=nombre_pais,
        nombre_estado=nombre_estado,
        nombre_localidad=nombre_localidad,
        nombre_organizacion=nombre_organizacion,
        nombre_comun=nombre_comun,
        dias_valido=dias_valido,
    )
    guardar_clave_y_certificado_en_pem(
        private_key,
        cert,
        ruta_carpeta=ruta_carpeta_ca,
        nombre_clave="ca_key.pem",
        nombre_cert="ca_cert.pem",
    )
    return private_key, cert