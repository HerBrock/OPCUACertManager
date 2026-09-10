"""
Batch Certificate Generator Module.

This module provides functionality to generate multiple certificates in batch mode.

Features:
- Import certificate list from CSV with enhanced format (v0.2.0).
- Generate certificates in a loop.
- Track progress and results.
- Handle errors gracefully.
- Validate CSV rows before processing.

CSV Format (v0.2.0):
    cert_name;Country;State/Province;Locality;Organization;CN;SAN;Validity days;key size
    Kepware_Server;US;California;Los Angeles;MyCompany;kepware-server.local;DNS:kepware,IP:192.168.1.100;365;2048
    Ignition_Client;ES;Madrid;Madrid;MyCompany;ignition-client;DNS:ignition;730;4096
"""

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any

from src.core.ca import create_ca
from src.core.server_cert import create_server_certificate
from src.core.client_cert import create_client_certificate
from src.core.project_manager import log_certificate


class CertType(Enum):
    """Certificate type enumeration."""
    SERVER = "server"
    CLIENT = "client"


@dataclass
class BatchCertificate:
    """Represents a certificate to be generated in batch mode."""
    nombre_certificado: str
    tipo: CertType
    country: str = "ES"
    state: str = "Madrid"
    locality: str = "Madrid"
    organization: str = "MiEmpresa"
    common_name: str = ""
    san_list: Optional[List[str]] = None
    validity_days: int = 365
    key_size: int = 2048


@dataclass
class BatchResult:
    """Result of a single certificate generation."""
    nombre_certificado: str
    tipo: str
    success: bool
    ruta_completa: Optional[str]
    error: Optional[str] = None


@dataclass
class BatchProgress:
    """Progress information for batch generation."""
    total: int
    current: int
    successes: int
    failures: int
    skipped: int
    cancelled: bool
    current_message: str


@dataclass
class ValidationError:
    """Represents a validation error for a CSV row."""
    row_number: int
    cert_name: str
    errors: List[str]


class BatchGenerator:
    """
    Batch certificate generator.

    Generates multiple certificates based on a list of certificate definitions.
    """

    def __init__(
        self,
        project_path: str | Path,
        ca_folder: str,
        output_folder: str,
        cert_type: CertType,
        country: str = "ES",
        state: str = "Madrid",
        locality: str = "Madrid",
        organization: str = "MiEmpresa",
        validity_days: int = 365,
        key_size: int = 2048,
    ):
        """
        Initialize batch generator.

        Parameters:
            project_path: Path to the project folder.
            ca_folder: Path to CA folder (for signing).
            output_folder: Folder where certificates will be saved.
            cert_type: Type of certificates to generate (server or client).
            country: Country for certificate subject.
            state: State/Province for certificate subject.
            locality: Locality for certificate subject.
            organization: Organization for certificate subject.
            validity_days: Validity period in days.
            key_size: RSA key size (2048 or 4096).
        """
        self.project_path = Path(project_path)
        self.ca_folder = ca_folder
        self.output_folder = output_folder
        self.cert_type = cert_type
        self.country = country
        self.state = state
        self.locality = locality
        self.organization = organization
        self.validity_days = validity_days
        self.key_size = key_size

        self.certificates: List[BatchCertificate] = []
        self.results: List[BatchResult] = []
        self.validation_errors: List[ValidationError] = []
        self.progress = BatchProgress(
            total=0,
            current=0,
            successes=0,
            failures=0,
            skipped=0,
            cancelled=False,
            current_message="",
        )

        # Callback for progress updates
        self.progress_callback: Optional[Callable[[BatchProgress], None]] = None

    def set_progress_callback(self, callback: Callable[[BatchProgress], None]):
        """
        Set callback function for progress updates.

        Parameters:
            callback: Function that receives BatchProgress object.
        """
        self.progress_callback = callback

    def _update_progress(self, message: str):
        """Update progress and notify callback."""
        self.progress.current_message = message
        if self.progress_callback:
            self.progress_callback(self.progress)

    def validate_row(self, row: Dict[str, str], row_number: int) -> Optional[ValidationError]:
        """
        Validate a single CSV row.

        Parameters:
            row: Dictionary with row data.
            row_number: Row number in CSV file.

        Returns:
            ValidationError if validation fails, None otherwise.
        """
        errors = []
        cert_name = row.get("cert_name", "").strip()

        # Check required fields
        required_fields = ["cert_name", "Country", "State/Province", "Locality", "Organization", "CN", "Validity days", "key size"]
        for field in required_fields:
            value = row.get(field, "").strip()
            if not value:
                errors.append(f"Missing required field: {field}")

        # Validate key size
        key_size_str = row.get("key size", "").strip()
        if key_size_str:
            try:
                key_size = int(key_size_str)
                if key_size not in [2048, 4096]:
                    errors.append("Key size must be 2048 or 4096")
            except ValueError:
                errors.append("Key size must be a number")

        # Validate validity days
        validity_str = row.get("Validity days", "").strip()
        if validity_str:
            try:
                validity = int(validity_str)
                if validity <= 0:
                    errors.append("Validity days must be greater than 0")
            except ValueError:
                errors.append("Validity days must be a number")

        if errors:
            return ValidationError(
                row_number=row_number,
                cert_name=cert_name or f"Row {row_number}",
                errors=errors,
            )

        return None

    def load_from_csv(self, csv_path: str | Path) -> tuple[int, List[ValidationError]]:
        """
        Load certificate list from CSV file (v0.2.0 format).

        Expected CSV format:
            cert_name;Country;State/Province;Locality;Organization;CN;SAN;Validity days;key size
            Kepware_Server;US;California;Los Angeles;MyCompany;kepware-server.local;DNS:kepware,IP:192.168.1.100;365;2048

        Parameters:
            csv_path: Path to CSV file.

        Returns:
            Tuple of (number of valid certificates loaded, list of validation errors).
        """
        csv_path = Path(csv_path)
        self.certificates = []
        self.validation_errors = []

        with open(csv_path, "r", encoding="utf-8") as f:
            # Use semicolon as delimiter
            reader = csv.DictReader(f, delimiter=";")

            for row_number, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                # Validate row
                validation_error = self.validate_row(row, row_number)

                if validation_error:
                    self.validation_errors.append(validation_error)
                    continue

                # Parse SAN field
                san_str = row.get("SAN", "").strip()
                san_list = None
                if san_str:
                    # SAN can be comma-separated or one per line
                    san_list = [s.strip() for s in san_str.split(",") if s.strip()]

                # Create certificate entry
                cert = BatchCertificate(
                    nombre_certificado=row.get("cert_name", "").strip(),
                    tipo=self.cert_type,
                    country=row.get("Country", "").strip(),
                    state=row.get("State/Province", "").strip(),
                    locality=row.get("Locality", "").strip(),
                    organization=row.get("Organization", "").strip(),
                    common_name=row.get("CN", "").strip(),
                    san_list=san_list,
                    validity_days=int(row.get("Validity days", "365").strip()),
                    key_size=int(row.get("key size", "2048").strip()),
                )
                self.certificates.append(cert)

        # Update progress
        self.progress.total = len(self.certificates)
        self.progress.current = 0
        self.progress.successes = 0
        self.progress.failures = 0
        self.progress.skipped = 0
        self.progress.cancelled = False

        valid_count = len(self.certificates)
        error_count = len(self.validation_errors)

        self._update_progress(f"Loaded {valid_count} valid certificates from CSV ({error_count} invalid rows)")

        return len(self.certificates), self.validation_errors

    def get_validation_summary(self) -> str:
        """
        Get summary of validation errors.

        Returns:
            Human-readable summary of validation errors.
        """
        if not self.validation_errors:
            return "All rows are valid."

        summary_lines = [f"Found {len(self.validation_errors)} invalid row(s):"]
        for error in self.validation_errors:
            summary_lines.append(f"  Row {error.row_number} ({error.cert_name}):")
            for err in error.errors:
                summary_lines.append(f"    - {err}")

        return "\n".join(summary_lines)

    def load_from_list(self, cert_list: List[dict]) -> int:
        """
        Load certificate list from a list of dictionaries.

        Parameters:
            cert_list: List of dicts with certificate data.

        Returns:
            Number of certificates loaded.
        """
        self.certificates = []

        for item in cert_list:
            cert = BatchCertificate(
                nombre_certificado=item.get("nombre_certificado", "").strip(),
                tipo=self.cert_type,
                country=item.get("country", "ES"),
                state=item.get("state", "Madrid"),
                locality=item.get("locality", "Madrid"),
                organization=item.get("organization", "MiEmpresa"),
                common_name=item.get("common_name", ""),
                san_list=item.get("san_list"),
                validity_days=item.get("validity_days", 365),
                key_size=item.get("key_size", 2048),
            )
            self.certificates.append(cert)

        # Update progress
        self.progress.total = len(self.certificates)
        self.progress.current = 0
        self.progress.successes = 0
        self.progress.failures = 0
        self.progress.skipped = 0
        self.progress.cancelled = False

        self._update_progress(f"Loaded {len(self.certificates)} certificates")

        return len(self.certificates)

    def generate_all(self) -> List[BatchResult]:
        """
        Generate all certificates in the list.

        Returns:
            List of BatchResult objects.
        """
        self.results = []
        self.progress.current = 0
        self.progress.successes = 0
        self.progress.failures = 0
        self.progress.skipped = 0
        self.progress.cancelled = False

        for cert in self.certificates:
            # Check if cancelled
            if self.progress.cancelled:
                break

            # Generate certificate
            result = self._generate_certificate(cert)
            self.results.append(result)

            # Update progress
            self.progress.current += 1
            if result.success:
                self.progress.successes += 1
            else:
                self.progress.failures += 1

            self._update_progress(
                f"Generated {cert.nombre_certificado}: {'✓' if result.success else '✗'}"
            )

        final_message = (
            f"Batch completed: {self.progress.successes} successes, "
            f"{self.progress.failures} failures"
        )
        self._update_progress(final_message)

        return self.results

    def _generate_certificate(self, cert: BatchCertificate) -> BatchResult:
        """
        Generate a single certificate.

        Parameters:
            cert: Certificate definition.

        Returns:
            BatchResult object.
        """
        try:
            if self.cert_type == CertType.SERVER:
                result = create_server_certificate(
                    server_folder=self.output_folder,
                    ca_folder=str(self.ca_folder),
                    key_size=cert.key_size,
                    country_name=cert.country,
                    state_name=cert.state,
                    locality_name=cert.locality,
                    organization_name=cert.organization,
                    common_name=cert.common_name,
                    san_list=cert.san_list,
                    validity_days=cert.validity_days,
                )

                cert_path = result.get("server_cert_path")

                if result["success"]:
                    # Log to CSV
                    log_certificate(
                        project_folder=self.project_path,
                        nombre_certificado=cert.nombre_certificado,
                        tipo="server",
                        ruta_completa=cert_path,
                        fecha_expiracion=result["fecha_expiracion"],
                        sujeto=result["sujeto"],
                        emisor=result["emisor"],
                        estado="created",
                    )

                return BatchResult(
                    nombre_certificado=cert.nombre_certificado,
                    tipo="server",
                    success=result["success"],
                    ruta_completa=cert_path,
                    error=result.get("error"),
                )

            elif self.cert_type == CertType.CLIENT:
                result = create_client_certificate(
                    client_folder=self.output_folder,
                    ca_folder=str(self.ca_folder),
                    key_size=cert.key_size,
                    country_name=cert.country,
                    state_name=cert.state,
                    locality_name=cert.locality,
                    organization_name=cert.organization,
                    common_name=cert.common_name,
                    san_list=cert.san_list,
                    validity_days=cert.validity_days,
                )

                cert_path = result.get("client_cert_path")

                if result["success"]:
                    # Log to CSV
                    log_certificate(
                        project_folder=self.project_path,
                        nombre_certificado=cert.nombre_certificado,
                        tipo="client",
                        ruta_completa=cert_path,
                        fecha_expiracion=result["fecha_expiracion"],
                        sujeto=result["sujeto"],
                        emisor=result["emisor"],
                        estado="created",
                    )

                return BatchResult(
                    nombre_certificado=cert.nombre_certificado,
                    tipo="client",
                    success=result["success"],
                    ruta_completa=cert_path,
                    error=result.get("error"),
                )

        except Exception as e:
            return BatchResult(
                nombre_certificado=cert.nombre_certificado,
                tipo=self.cert_type.value,
                success=False,
                ruta_completa=None,
                error=str(e),
            )

    def cancel(self):
        """Cancel batch generation."""
        self.progress.cancelled = True
        self._update_progress("Batch generation cancelled by user")

    def get_summary(self) -> dict:
        """
        Get summary of batch generation.

        Returns:
            Dictionary with summary statistics.
        """
        return {
            "total": self.progress.total,
            "successes": self.progress.successes,
            "failures": self.progress.failures,
            "skipped": self.progress.skipped,
            "cancelled": self.progress.cancelled,
            "success_rate": (
                self.progress.successes / self.progress.total * 100
                if self.progress.total > 0
                else 0
            ),
        }


def import_batch_csv(csv_path: str | Path) -> tuple[List[dict], List[ValidationError]]:
    """
    Import batch certificate list from CSV file (v0.2.0 format).

    Expected CSV format:
        cert_name;Country;State/Province;Locality;Organization;CN;SAN;Validity days;key size

    Parameters:
        csv_path: Path to CSV file.

    Returns:
        Tuple of (list of valid certificate dicts, list of validation errors).
    """
    csv_path = Path(csv_path)
    cert_list = []
    validation_errors = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row_number, row in enumerate(reader, start=2):
            # Basic validation
            errors = []
            cert_name = row.get("cert_name", "").strip()

            required_fields = ["cert_name", "Country", "State/Province", "Locality", "Organization", "CN", "Validity days", "key size"]
            for field in required_fields:
                if not row.get(field, "").strip():
                    errors.append(f"Missing: {field}")

            if errors:
                validation_errors.append(ValidationError(
                    row_number=row_number,
                    cert_name=cert_name or f"Row {row_number}",
                    errors=errors,
                ))
                continue

            # Parse SAN
            san_str = row.get("SAN", "").strip()
            san_list = [s.strip() for s in san_str.split(",") if s.strip()] if san_str else None

            cert_list.append({
                "nombre_certificado": cert_name,
                "country": row.get("Country", "").strip(),
                "state": row.get("State/Province", "").strip(),
                "locality": row.get("Locality", "").strip(),
                "organization": row.get("Organization", "").strip(),
                "common_name": row.get("CN", "").strip(),
                "san_list": san_list,
                "validity_days": int(row.get("Validity days", "365").strip()),
                "key_size": int(row.get("key size", "2048").strip()),
            })

    return cert_list, validation_errors
