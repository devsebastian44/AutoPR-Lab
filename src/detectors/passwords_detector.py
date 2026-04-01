"""
AutoPR Lab - Passwords Detector
=================================
Detecta contraseñas hardcodeadas y credenciales inseguras en el código.
"""

import re

from detectors.base_detector import BaseDetector, DetectorResult, DetectorStatus


class PasswordsDetector(BaseDetector):
    """
    Detecta contraseñas y credenciales hardcodeadas en asignaciones directas.
    Analiza patrones como: password = "secret123", pwd = "admin"
    """

    # Patrones de asignación de contraseñas
    ASSIGNMENT_PATTERNS = [
        # password = "value" en múltiples formatos
        (
            r"""(password|passwd|pwd|pass|secret|credential|cred|auth_token|access_token)\s*[:=]\s*['"]([^'"]{4,})['"]""",
            "Password hardcodeado",
        ),
        # En JSON/YAML
        (
            r"""['"](password|passwd|pwd|pass|secret|token|api_key|auth)['"]\s*:\s*['"]([^'"]{4,})['"]""",
            "Credencial en configuración",
        ),
        # Conexiones a base de datos
        (
            r"""(db_pass|database_password|db_password|mysql_pass|mongo_pass)\s*[:=]\s*['"]([^'"]{4,})['"]""",
            "Contraseña de base de datos",
        ),
        # Tokens en código
        (
            r"""(auth_token|access_token|refresh_token|secret_key|signing_key)\s*[:=]\s*['"]([^'"]{8,})['"]""",
            "Token de autenticación hardcodeado",
        ),
        # Variables de entorno hardcodeadas dentro del código (no en .env)
        (
            r"""os\.environ\[['"](password|secret|token|key)['"]\]\s*=\s*['"]([^'"]{4,})['"]""",
            "Asignación directa de variable de entorno sensible",
        ),
    ]

    # Contraseñas triviales/débiles que siempre son un error
    TRIVIAL_PASSWORDS = {
        "password",
        "123456",
        "12345678",
        "qwerty",
        "admin",
        "root",
        "welcome",
        "letmein",
        "monkey",
        "dragon",
        "master",
        "password1",
        "abc123",
        "test",
        "testing",
        "changeme",
        "default",
        "pass",
        "secret",
        "1234",
        "1111",
        "0000",
        "admin123",
        "pass123",
    }

    # Patrones a ignorar (falsos positivos)
    FALSE_POSITIVE_PATTERNS = [
        r"^\s*#",  # Comentarios
        r"^\s*//",  # Comentarios JS
        r"example\.com",  # Ejemplos
        r"your[-_]?password",  # Instrucciones
        r"your[-_]?",  # Cualquier YOUR_ prefix
        r"<password>",  # Placeholders XML
        r"\$\{[^}]+\}",  # Variables en templates
        r"os\.getenv\(",  # Lectura de env vars
        r"environ\.get\(",  # Lectura de env vars
        r"process\.env\.",  # Node.js env vars
        r"getenv\(",  # C/PHP getenv
        r"config\[",  # Acceso a config objects
        r"settings\.",  # Django settings
        r"# noqa",  # Exclusiones explícitas
        r"# nosec",  # Exclusiones de bandit
        r"CHANGE_ME",  # Placeholder explícito
        r"REPLACE_",  # Placeholder explícito
        r"_HERE",  # Placeholder tipo KEY_HERE
        r"placeholder",  # Palabra placeholder
        r"<[A-Z_]+>",  # Placeholders tipo <MY_KEY>
    ]

    @property
    def name(self) -> str:
        return "PasswordsDetector"

    @property
    def description(self) -> str:
        return "Detecta contraseñas hardcodeadas y credenciales débiles en el código fuente"

    @property
    def severity(self) -> str:
        return "critical"

    def _is_false_positive(self, line: str) -> bool:
        for pattern in self.FALSE_POSITIVE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False

    def _check_trivial_password(self, value: str) -> bool:
        return value.strip().lower() in self.TRIVIAL_PASSWORDS

    def analyze(self, file_path: str, content: str) -> list[DetectorResult]:
        if self.should_skip(file_path):
            return []

        results = []
        lines = content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            if self._is_false_positive(line):
                continue

            for pattern, description in self.ASSIGNMENT_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    variable_name = groups[0] if groups else "unknown"
                    secret_value = groups[-1] if len(groups) > 1 else ""

                    # Verificar si es una contraseña trivial (aún más crítico)
                    is_trivial = self._check_trivial_password(secret_value)

                    status = DetectorStatus.ERROR
                    details = [
                        f"Variable: `{variable_name}`",
                        f"Valor detectado: `{'*' * len(secret_value)}`",
                        "🔒 Usa variables de entorno o un secrets manager (Vault, AWS Secrets Manager, etc.)",
                    ]

                    if is_trivial:
                        details.append(
                            f"⚠️ CRÍTICO: La contraseña '{secret_value}' es trivialmente débil y conocida"
                        )

                    results.append(
                        DetectorResult(
                            status=status,
                            detector_name=self.name,
                            message=f"{description} en variable '{variable_name}'",
                            details=details,
                            file_path=file_path,
                            line_number=line_num,
                        )
                    )
                    break

        return results
