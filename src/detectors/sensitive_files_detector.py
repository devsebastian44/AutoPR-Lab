"""
AutoPR Lab - Sensitive Files Detector
=======================================
Detecta archivos sensibles incluidos accidentalmente en el PR:
.env, config secrets, private keys, certificados, etc.
"""

import os
import re

from detectors.base_detector import BaseDetector, DetectorResult, DetectorStatus


class SensitiveFilesDetector(BaseDetector):
    """
    Detecta si el PR incluye archivos que NUNCA deberían estar en un repositorio.
    Analiza el nombre del archivo y su contenido.
    """

    # Archivos que NUNCA deben aparecer en un PR
    FORBIDDEN_FILES = {
        # Variables de entorno
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        ".env.staging",
        ".env.test",
        ".env.backup",
        # Configuraciones de secretos
        "secrets.yml",
        "secrets.yaml",
        "secrets.json",
        "credentials.json",
        "credentials.yml",
        "config.secret.yml",
        "config.secret.json",
        "local_settings.py",  # Django
        # Claves privadas y certificados
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        "id_rsa.pub",
        "id_ecdsa.pub",
        "id_ed25519.pub",
        "private.key",
        "private.pem",
        "server.key",
        "client.key",
        "ca.key",
        "*.pfx",
        "*.p12",
        "keystore.jks",
        # Archivos de bases de datos
        "*.sqlite",
        "*.sqlite3",
        "*.db",
        "dump.sql",
        "backup.sql",
        "database.sql",
        # Configuración de servicios cloud
        ".aws/credentials",
        ".aws/config",
        "gcloud-key.json",
        "service-account.json",
        "firebase-adminsdk*.json",
        "firebase.json",
        "google-services.json",
        # Archivos de configuración local de IDEs con datos sensibles
        ".idea/workspace.xml",
        "*.suo",  # Visual Studio
        # Terraform state (puede contener secretos)
        "terraform.tfstate",
        "terraform.tfstate.backup",
        "*.tfvars",  # Excepto ejemplo: *.tfvars.example
        # Archivos de contraseñas
        "htpasswd",
        ".htpasswd",
        "passwd",
        "shadow",
    }

    # Extensiones siempre prohibidas
    FORBIDDEN_EXTENSIONS = {
        ".pem",
        ".key",
        ".pfx",
        ".p12",
        ".jks",
        ".pkcs12",
        ".crt",
        ".cer",
        ".der",
    }

    # Patrones en el contenido que indican archivo sensible
    SENSITIVE_CONTENT_PATTERNS = [
        (r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "Clave privada PEM"),
        (r"-----BEGIN CERTIFICATE-----", "Certificado SSL/TLS"),
        (r"-----BEGIN PGP PRIVATE KEY BLOCK-----", "Clave privada PGP"),
        # .env con valores reales (no placeholders)
        (
            r"(?m)^(export\s+)?[A-Z_]*(PASSWORD|SECRET|TOKEN|KEY|API_KEY)\s*=\s*(?!YOUR_|your_|<|CHANGE_ME|REPLACE|example|placeholder|xxx|none|null|false|true|\$\{)[^\s\$<\"']{6,}",
            ".env con valores reales",
        ),
        (r"\[default\]\s*\naws_access_key_id", "Archivo de credenciales AWS"),
        (r'"type"\s*:\s*"service_account"', "Clave de servicio de Google"),
    ]

    # Advertencias: archivos que podrían ser sensibles según contexto
    WARNING_FILES = {
        ".env.example",
        ".env.template",
        ".env.sample",
        "config.example.yml",
        "settings.example.py",
    }

    @property
    def name(self) -> str:
        return "SensitiveFilesDetector"

    @property
    def description(self) -> str:
        return "Detecta archivos sensibles (.env, keys, certificados) que no deben estar en el repositorio"

    @property
    def severity(self) -> str:
        return "critical"

    def should_skip(self, file_path: str) -> bool:
        # Este detector NO omite ningún archivo por extensión
        return False

    def _get_filename(self, file_path: str) -> str:
        return os.path.basename(file_path).lower()

    def _is_forbidden_file(self, file_path: str) -> bool:
        filename = self._get_filename(file_path)
        file_path_lower = file_path.lower()
        filename_lower = filename.lower()

        # Si está en WARNING_FILES, no es forbidden (tiene su propio tratamiento)
        if self._is_warning_file(file_path):
            return False

        # Verificar nombre exacto contra la lista de prohibidos
        forbidden_lower = {f.lower() for f in self.FORBIDDEN_FILES if "*" not in f}
        if filename_lower in forbidden_lower:
            return True

        # Verificar rutas específicas con path separator (ej: .aws/credentials)
        for forbidden in self.FORBIDDEN_FILES:
            if "/" in forbidden and forbidden.lower() in file_path_lower:
                return True

        # Verificar extensión
        _, ext = os.path.splitext(filename)
        if ext in self.FORBIDDEN_EXTENSIONS:
            return True

        # Verificar patrones con wildcards
        for forbidden in self.FORBIDDEN_FILES:
            if "*" in forbidden:
                pattern = r"^" + forbidden.replace(".", r"\.").replace("*", ".*") + r"$"
                if re.match(pattern, filename, re.IGNORECASE):
                    return True

        return False

    def _is_warning_file(self, file_path: str) -> bool:
        filename = self._get_filename(file_path)
        return filename in {f.lower() for f in self.WARNING_FILES}

    def analyze(self, file_path: str, content: str) -> list[DetectorResult]:
        results = []
        filename = self._get_filename(file_path)

        # ERROR: Archivo completamente prohibido
        if self._is_forbidden_file(file_path):
            results.append(
                DetectorResult(
                    status=DetectorStatus.ERROR,
                    detector_name=self.name,
                    message=f"Archivo sensible prohibido: `{filename}`",
                    details=[
                        f"Ruta detectada: `{file_path}`",
                        "🚫 Este tipo de archivo NUNCA debe estar en el repositorio.",
                        "💡 Agrégalo a .gitignore inmediatamente.",
                        "🔐 Si ya fue expuesto: rota todas las credenciales involucradas.",
                    ],
                    file_path=file_path,
                )
            )
            return results

        # WARNING: Archivo de ejemplo/template (puede ser intencional)
        if self._is_warning_file(file_path):
            # Verificar que no tenga valores reales
            has_real_values = any(
                re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                for pattern, _ in self.SENSITIVE_CONTENT_PATTERNS
            )

            if has_real_values:
                results.append(
                    DetectorResult(
                        status=DetectorStatus.ERROR,
                        detector_name=self.name,
                        message=f"Archivo de template con valores reales: `{filename}`",
                        details=[
                            "El archivo parece un template (.example/.sample) pero contiene valores reales.",
                            "Reemplaza los valores reales con placeholders: ${YOUR_SECRET_HERE}",
                        ],
                        file_path=file_path,
                    )
                )
            else:
                results.append(
                    DetectorResult(
                        status=DetectorStatus.WARNING,
                        detector_name=self.name,
                        message=f"Archivo de template detectado: `{filename}`",
                        details=[
                            "Este archivo de ejemplo/template es aceptable si solo contiene placeholders.",
                            "✅ Asegúrate de que los valores sean ficticios (ej: YOUR_API_KEY_HERE).",
                        ],
                        file_path=file_path,
                    )
                )
            return results

        # Analizar contenido de cualquier archivo
        for pattern, description in self.SENSITIVE_CONTENT_PATTERNS:
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if match:
                line_num = content[: match.start()].count("\n") + 1
                results.append(
                    DetectorResult(
                        status=DetectorStatus.ERROR,
                        detector_name=self.name,
                        message=f"Contenido sensible en `{filename}`: {description}",
                        details=[
                            f"Patrón encontrado en línea {line_num}",
                            "🔐 El contenido de este archivo no debe estar en el repositorio.",
                        ],
                        file_path=file_path,
                        line_number=line_num,
                    )
                )

        return results
