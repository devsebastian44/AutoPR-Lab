"""
Ejemplo de PR VÁLIDO — Nuevo detector de SQL Injection
=======================================================
Este archivo representa un PR que AutoPR Lab ACEPTARÁ y mergeará automáticamente.

✅ Está en /detectors/ (ruta permitida)
✅ Hereda de BaseDetector
✅ No tiene imports peligrosos
✅ Implementa todos los métodos requeridos
✅ No contiene secretos ni credenciales
"""

import re

from detectors.base_detector import BaseDetector, DetectorResult, DetectorStatus


class SQLInjectionDetector(BaseDetector):
    """
    Detecta posibles vulnerabilidades de SQL Injection en el código.
    Busca queries construidas por concatenación o f-strings en lugar de
    parámetros preparados (prepared statements).
    """

    # Patrones de SQL injection potencial
    PATTERNS = [
        # f-strings con SQL
        (
            r'f["\'].*?(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE).*?\{',
            "SQL con f-string",
        ),
        # Concatenación de strings con SQL
        (
            r'["\'].*?(SELECT|INSERT|UPDATE|DELETE).*?["\']\s*\+\s*\w+',
            "SQL con concatenación",
        ),
        # format() en queries SQL
        (
            r'["\'].*?(SELECT|INSERT|UPDATE|DELETE).*?["\']\.format\(',
            "SQL con .format()",
        ),
        # % formatting en queries SQL
        (r'["\'].*?(SELECT|INSERT|UPDATE|DELETE).*?%\s*[\(\w]', "SQL con % formatting"),
        # execute() con concatenación directa (peligroso)
        (r'\.execute\s*\(\s*["\'].*?\+', "execute() con concatenación"),
        (r'\.execute\s*\(\s*f["\']', "execute() con f-string"),
    ]

    # Patrones seguros (prepared statements / parameterized queries)
    SAFE_PATTERNS = [
        r"\.execute\s*\(\s*['\"].*?\?",  # SQLite/MySQL con ?
        r"\.execute\s*\(\s*['\"].*?%s",  # psycopg2 con %s
        r"\.execute\s*\(\s*['\"].*?:\w+",  # SQLAlchemy con :param
        r"text\(['\"]",  # SQLAlchemy text()
        r"sqlalchemy",  # SQLAlchemy en general
    ]

    SQL_FILE_EXTENSIONS = {".py", ".js", ".ts", ".php", ".rb", ".java", ".cs", ".go"}

    @property
    def name(self) -> str:
        return "SQLInjectionDetector"

    @property
    def description(self) -> str:
        return "Detecta posibles vulnerabilidades de SQL Injection por concatenación de strings"

    @property
    def severity(self) -> str:
        return "critical"

    def should_skip(self, file_path: str) -> bool:
        if super().should_skip(file_path):
            return True
        _, ext = file_path.rsplit(".", 1) if "." in file_path else (file_path, "")
        return f".{ext}" not in self.SQL_FILE_EXTENSIONS

    def _has_safe_pattern(self, line: str) -> bool:
        return any(re.search(p, line, re.IGNORECASE) for p in self.SAFE_PATTERNS)

    def analyze(self, file_path: str, content: str) -> list[DetectorResult]:
        if self.should_skip(file_path):
            return []

        results = []
        lines = content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            if self._has_safe_pattern(line):
                continue
            if line.strip().startswith("#") or line.strip().startswith("//"):
                continue

            for pattern, description in self.PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    results.append(
                        DetectorResult(
                            status=DetectorStatus.ERROR,
                            detector_name=self.name,
                            message=f"Posible SQL Injection: {description}",
                            details=[
                                f"Línea problemática: `{line.strip()[:100]}`",
                                "🔒 Usa prepared statements o parámetros vinculados:",
                                "  ✅ cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
                                "  ✅ cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                                "  ❌ cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
                            ],
                            file_path=file_path,
                            line_number=line_num,
                        )
                    )
                    break

        return results
