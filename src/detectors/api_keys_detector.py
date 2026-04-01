"""
AutoPR Lab - API Keys Detector
================================
Detecta API keys, tokens y credenciales expuestas en el código fuente.
"""

import re

from detectors.base_detector import BaseDetector, DetectorResult, DetectorStatus


class APIKeysDetector(BaseDetector):
    """
    Detecta patrones conocidos de API keys y tokens en el código.
    Cubre: AWS, GCP, GitHub, Stripe, Twilio, OpenAI, HuggingFace, etc.
    """

    # Formato: (nombre_servicio, regex_pattern)
    PATTERNS = [
        # AWS
        ("AWS Access Key", r"(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])"),
        (
            "AWS Secret Key",
            r"(?i)aws.{0,20}?['\":]?\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
        ),
        # GitHub
        ("GitHub Token (classic)", r"ghp_[a-zA-Z0-9]{36}"),
        ("GitHub OAuth Token", r"gho_[a-zA-Z0-9]{36}"),
        ("GitHub Actions Token", r"ghs_[a-zA-Z0-9]{36}"),
        ("GitHub Fine-grained Token", r"github_pat_[a-zA-Z0-9_]{82}"),
        # Google / GCP
        ("Google API Key", r"AIza[0-9A-Za-z\-_]{35}"),
        ("Google OAuth", r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com"),
        # Stripe
        ("Stripe Live Key", r"sk_live_[0-9a-zA-Z]{24,}"),
        ("Stripe Test Key", r"sk_test_[0-9a-zA-Z]{24,}"),
        # Twilio
        ("Twilio Account SID", r"AC[a-zA-Z0-9]{32}"),
        (
            "Twilio Auth Token",
            r"(?i)twilio.{0,20}?['\":]?\s*['\"]?([a-f0-9]{32})['\"]?",
        ),
        # OpenAI
        ("OpenAI API Key", r"sk-[a-zA-Z0-9]{20,60}"),
        ("OpenAI Org Key", r"org-[a-zA-Z0-9]{24}"),
        # HuggingFace
        ("HuggingFace Token", r"hf_[a-zA-Z0-9]{37}"),
        # Anthropic
        ("Anthropic API Key", r"sk-ant-[a-zA-Z0-9\-_]{95}"),
        # Generic secrets
        (
            "Generic API Key Pattern",
            r"(?i)api[_\-\s]?key\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
        ),
        ("Generic Bearer Token", r"(?i)bearer\s+[a-zA-Z0-9\-._~+/]+=*"),
        ("Generic Authorization Header", r"(?i)authorization\s*:\s*['\"]?.{15,}['\"]?"),
        # Private keys (PEM format)
        ("RSA Private Key", r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----"),
        ("SSH Private Key", r"-----BEGIN OPENSSH PRIVATE KEY-----"),
        ("PGP Private Key", r"-----BEGIN PGP PRIVATE KEY BLOCK-----"),
        # Database connection strings
        (
            "Database URL with credentials",
            r"(?i)(mongodb|postgresql|mysql|redis):\/\/[^:]+:[^@]+@",
        ),
        ("JDBC Connection String", r"(?i)jdbc:[a-z]+:\/\/[^;]+;(user|password)=[^;]+"),
    ]

    # Líneas que se deben ignorar (falsos positivos comunes)
    SAFE_PATTERNS = [
        r"^\s*#",  # Comentarios Python/Shell
        r"^\s*//",  # Comentarios JS/Java
        r"example",  # Ejemplos explícitos
        r"placeholder",  # Placeholders
        r"your[_-]?key",  # Instrucciones de uso
        r"<YOUR_",  # Templates
        r"\$\{",  # Variables de entorno en templates
        r"os\.getenv",  # Lectura de variables de entorno (seguro)
        r"environ\.get",  # Lectura de variables de entorno (seguro)
        r"process\.env\.",  # Variables de entorno Node.js (seguro)
        r"\"\"\"",  # Docstrings
    ]

    BINARY_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".ico",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".bin",
        ".exe",
        ".whl",
    }

    @property
    def name(self) -> str:
        return "APIKeysDetector"

    @property
    def description(self) -> str:
        return (
            "Detecta API keys, tokens y credenciales hardcodeadas en el código fuente"
        )

    @property
    def severity(self) -> str:
        return "critical"

    def should_skip(self, file_path: str) -> bool:
        if super().should_skip(file_path):
            return True
        # Ignorar archivos de lock y dependencias
        skip_paths = ["package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock"]
        return any(skip in file_path for skip in skip_paths)

    def _is_safe_line(self, line: str) -> bool:
        """Verifica si una línea coincide con patrones seguros (falsos positivos)."""
        for safe_pattern in self.SAFE_PATTERNS:
            if re.search(safe_pattern, line, re.IGNORECASE):
                return True
        return False

    def analyze(self, file_path: str, content: str) -> list[DetectorResult]:
        if self.should_skip(file_path):
            return []

        results = []
        lines = content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            if self._is_safe_line(line):
                continue

            for service_name, pattern in self.PATTERNS:
                match = re.search(pattern, line)
                if match:
                    # Ocultar el valor real en el reporte
                    detected_value = match.group(0)
                    masked = self._mask_secret(detected_value)

                    results.append(
                        DetectorResult(
                            status=DetectorStatus.ERROR,
                            detector_name=self.name,
                            message=f"Posible {service_name} detectado",
                            details=[
                                f"Patrón detectado: `{masked}`",
                                f"Línea completa: `{line.strip()[:80]}...`"
                                if len(line) > 80
                                else f"Línea: `{line.strip()}`",
                                "⚠️ Nunca hardcodees credenciales. Usa variables de entorno o un secrets manager.",
                            ],
                            file_path=file_path,
                            line_number=line_num,
                        )
                    )
                    break  # Un problema por línea es suficiente

        return results

    def _mask_secret(self, secret: str) -> str:
        """Enmascara un secreto para el reporte (muestra solo inicio y fin)."""
        if len(secret) <= 8:
            return "*" * len(secret)
        visible = 4
        return secret[:visible] + "*" * (len(secret) - visible * 2) + secret[-visible:]
