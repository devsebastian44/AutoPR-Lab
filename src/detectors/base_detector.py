"""
AutoPR Lab - Base Detector
==========================
Clase base para todos los detectores del sistema.
Todo detector nuevo DEBE heredar de esta clase.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DetectorStatus(StrEnum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class DetectorResult:
    """Resultado estándar de un detector."""

    status: DetectorStatus
    detector_name: str
    message: str
    details: list[str] = field(default_factory=list)
    file_path: str | None = None
    line_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "detector_name": self.detector_name,
            "message": self.message,
            "details": self.details,
            "file_path": self.file_path,
            "line_number": self.line_number,
        }

    def __str__(self) -> str:
        icon_map: dict[str, str] = {"OK": "✅", "WARNING": "⚠️", "ERROR": "❌"}
        icon = icon_map.get(self.status.value, "?")
        base = f"{icon} [{self.status.value}] {self.detector_name}: {self.message}"
        if self.file_path:
            base += f" (file: {self.file_path}"
            if self.line_number:
                base += f", line: {self.line_number}"
            base += ")"
        return base


class BaseDetector(ABC):
    """
    Clase base abstracta para todos los detectores de AutoPR Lab.

    Para agregar un detector nuevo:
    1. Crea un archivo en /detectors/mi_detector.py
    2. Hereda de BaseDetector
    3. Implementa el método `analyze`
    4. El sistema lo detectará automáticamente

    Ver: docs/how-to-add-detector.md
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre único del detector (usado en reportes)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Descripción breve de qué analiza este detector."""
        raise NotImplementedError

    @property
    def severity(self) -> str:
        """Nivel de severidad por defecto: 'critical', 'high', 'medium', 'low'."""
        return "high"

    @abstractmethod
    def analyze(self, file_path: str, content: str) -> list[DetectorResult]:
        """
        Analiza el contenido de un archivo.
        ...
        """
        raise NotImplementedError

    def should_skip(self, file_path: str) -> bool:
        """
        Define si este detector debe ignorar un archivo.
        Override para personalizar (ej: ignorar archivos de tests).
        """
        skip_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".ico",
            ".svg",
            ".pdf",
            ".zip",
            ".tar",
            ".gz",
            ".bin",
            ".lock",
        }
        return any(file_path.endswith(ext) for ext in skip_extensions)
