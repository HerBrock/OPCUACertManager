"""
Batch Certificate Generator Module.

This module provides functionality to generate multiple certificates in batch mode.

Features:
- Import certificate list from CSV.
- Generate certificates in a loop.
- Track progress and results.
- Handle errors gracefully.
"""

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Callable

from .ca import create_ca
from .server_cert import create_server_certificate
from .client_cert import create_client_certificate
from .project_manager import log_certificate


class CertType(Enum):
    """Certificate type enumeration."""
    SERVER = "server"
    CLIENT = "client"


@dataclass
class BatchCertificate:
    """Represents a certificate to be generated in batch mode."""
    nombre_certificado: str
    tipo: CertType
    cantidad: int = 1
    
    def __post_init__(self):
        if isinstance(self.tipo, str):
            self.tipo = CertType(self.tipo.lower())


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
    
    def load_from_csv(self, csv_path: str | Path) -> int:
        """
        Load certificate list from CSV file.
        
        Expected CSV format:
            nombre_certificado,cantidad
            cert_001,1
            cert_002,5
        
        Parameters:
            csv_path: Path to CSV file.
        
        Returns:
            Number of certificates loaded.
        """
        csv_path = Path(csv_path)
        self.certificates = []
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nombre = row.get("nombre_certificado", "").strip()
                cantidad_str = row.get("cantidad", "1").strip()
                
                if not nombre:
                    continue
                
                try:
                    cantidad = int(cantidad_str) if cantidad_str else 1
                except ValueError:
                    cantidad = 1
                
                # Create individual certificate entries
                for i in range(cantidad):
                    cert_name = f"{nombre}_{i+1:03d}" if cantidad > 1 else nombre
                    self.certificates.append(BatchCertificate(
                        nombre_certificado=cert_name,
                        tipo=self.cert_type,
                        cantidad=1,
                    ))
        
        # Update progress
        self.progress.total = len(self.certificates)
        self.progress.current = 0
        self.progress.successes = 0
        self.progress.failures = 0
        self.progress.skipped = 0
        self.progress.cancelled = False
        
        self._update_progress(f"Loaded {len(self.certificates)} certificates from CSV")
        
        return len(self.certificates)
    
    def load_from_list(self, cert_list: List[dict]) -> int:
        """
        Load certificate list from a list of dictionaries.
        
        Parameters:
            cert_list: List of dicts with keys: nombre_certificado, cantidad.
        
        Returns:
            Number of certificates loaded.
        """
        self.certificates = []
        
        for item in cert_list:
            nombre = item.get("nombre_certificado", "").strip()
            cantidad = item.get("cantidad", 1)
            
            if not nombre:
                continue
            
            # Create individual certificate entries
            for i in range(cantidad):
                cert_name = f"{nombre}_{i+1:03d}" if cantidad > 1 else nombre
                self.certificates.append(BatchCertificate(
                    nombre_certificado=cert_name,
                    tipo=self.cert_type,
                    cantidad=1,
                ))
        
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
            # Common name for certificate
            common_name = cert.nombre_certificado
            
            if self.cert_type == CertType.SERVER:
                result = create_server_certificate(
                    server_folder=self.output_folder,
                    ca_folder=str(self.ca_folder),
                    key_size=self.key_size,
                    country_name=self.country,
                    state_name=self.state,
                    locality_name=self.locality,
                    organization_name=self.organization,
                    common_name=common_name,
                    san_list=None,
                    validity_days=self.validity_days,
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
                    key_size=self.key_size,
                    country_name=self.country,
                    state_name=self.state,
                    locality_name=self.locality,
                    organization_name=self.organization,
                    common_name=common_name,
                    san_list=None,
                    validity_days=self.validity_days,
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


def import_batch_csv(csv_path: str | Path) -> List[dict]:
    """
    Import batch certificate list from CSV file.
    
    Expected CSV format:
        nombre_certificado,cantidad
        cert_001,1
        cert_002,5
    
    Parameters:
        csv_path: Path to CSV file.
    
    Returns:
        List of dictionaries with keys: nombre_certificado, cantidad.
    """
    csv_path = Path(csv_path)
    cert_list = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nombre = row.get("nombre_certificado", "").strip()
            cantidad_str = row.get("cantidad", "1").strip()
            
            if not nombre:
                continue
            
            try:
                cantidad = int(cantidad_str) if cantidad_str else 1
            except ValueError:
                cantidad = 1
            
            cert_list.append({
                "nombre_certificado": nombre,
                "cantidad": cantidad,
            })
    
    return cert_list