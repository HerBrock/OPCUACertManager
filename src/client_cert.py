"""
Módulo para crear certificados de cliente OPC UA.

Estos certificados serán firmados por la CA creada en ca.py.
"""

import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from .utils import cargar_ca_desde_disk, guardar_clave_y_certificado_en_pem


def generar_clave_cliente(tamano_clave: int = 2048) -> rsa.RSAPrivateKey:
    """
    Genera una clave privada RSA para el cliente OPC UA.
    """
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=tamano_clave,
    )


def construir_certificado_cliente(
    private_key_cliente: rsa.RSAPrivateKey,
    ca_private_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    nombre_pais: str = "ES",
    nombre_estado: str = "Madrid",
    nombre_localidad: str = "Madrid",
    nombre_organizacion: str = "MiEmpresa",
    nombre_comun: str = "cliente-opcua",
    nombres_alternos: Optional[List[str]] = None,
    dias_valido: int = 365,
) -> x509.Certificate:
    """
    Construye un certificado X.509 para un cliente OPC UA, firmado por la CA.
    """
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, nombre_pais),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, nombre_estado),
        x509.NameAttribute(NameOID.LOCALITY_NAME, nombre_localidad),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, nombre_organizacion),
        x509.NameAttribute(NameOID.COMMON_NAME, nombre_comun),
    ])

    issuer = ca_cert.subject

    ahora = datetime.now(timezone.utc)
    not_valid_before = ahora
    not_valid_after = ahora + timedelta(days=dias_valido)

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key_cliente.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before)
        .not_valid_after(not_valid_after)
    )

    # Basic Constraints: NO es una CA
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
            x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
        ]),
        critical=False,
    )

    # Subject Alternative Name (SAN)
    if nombres_alternos:
        san_list = []
        for nombre in nombres_alternos:
            nombre = nombre.strip()
            if nombre.upper().startswith("DNS:"):
                dns_name = nombre.split(":", 1)[1].strip()
                san_list.append(x509.DNSName(dns_name))
            elif nombre.upper().startswith("IP:"):
                ip_str = nombre.split(":", 1)[1].strip()
                ip_obj = ipaddress.ip_address(ip_str)
                san_list.append(x509.IPAddress(ip_obj))
            else:
                san_list.append(x509.DNSName(nombre))

        builder = builder.add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        )

    cert = builder.sign(ca_private_key, hashes.SHA256())
    return cert


def crear_certificado_cliente(
    ruta_carpeta_cliente: str | Path = "certs/client",
    ruta_carpeta_ca: str | Path = "certs/ca",
    tamano_clave: int = 2048,
    nombre_pais: str = "ES",
    nombre_estado: str = "Madrid",
    nombre_localidad: str = "Madrid",
    nombre_organizacion: str = "MiEmpresa",
    nombre_comun: str = "cliente-opcua",
    nombres_alternos: Optional[List[str]] = None,
    dias_valido: int = 365,
) -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """
    Función de alto nivel que:
    1. Carga la CA desde disco.
    2. Genera la clave del cliente.
    3. Construye el certificado del cliente firmado por la CA.
    4. Guarda clave y certificado en disco.

    Devuelve la clave y el certificado del cliente.
    """
    ca_private_key, ca_cert = cargar_ca_desde_disk(ruta_carpeta_ca)

    private_key_cliente = generar_clave_cliente(tamano_clave)

    cert = construir_certificado_cliente(
        private_key_cliente=private_key_cliente,
        ca_private_key=ca_private_key,
        ca_cert=ca_cert,
        nombre_pais=nombre_pais,
        nombre_estado=nombre_estado,
        nombre_localidad=nombre_localidad,
        nombre_organizacion=nombre_organizacion,
        nombre_comun=nombre_comun,
        nombres_alternos=nombres_alternos,
        dias_valido=dias_valido,
    )

    guardar_clave_y_certificado_en_pem(
        private_key_cliente,
        cert,
        ruta_carpeta=ruta_carpeta_cliente,
        nombre_clave="client_key.pem",
        nombre_cert="client_cert.pem",
    )

    return private_key_cliente, cert