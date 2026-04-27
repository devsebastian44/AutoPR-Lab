"""
AutoPR Lab - Core Scanner
===========================
Motor principal de análisis de Pull Requests.
Orquesta todos los detectores y genera el reporte final.
"""

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from detectors import discover_detectors
from detectors.base_detector import DetectorResult, DetectorStatus
from utils.logger import get_logger

logger = get_logger("scanner")


@dataclass
class ScanResult:
    """Resultado completo del análisis de un PR."""

    # Estado global del PR
    global_status: str  # "OK" | "WARNING" | "ERROR"
    decision: str  # "MERGE" | "WARN_MERGE" | "REJECT"

    # Métricas del PR
    pr_number: int
    files_analyzed: int
    total_findings: int
    errors: int
    warnings: int
    ok_count: int

    # Resultados por archivo
    findings: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    scan_duration_ms: float = 0.0
    detectors_run: list[str] = field(default_factory=list)
    timestamp: str = ""

    # Validación de seguridad del PR (path rules)
    path_validation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class SecurityRules:
    """
    Reglas de seguridad para el auto-merge.
    Define qué archivos y condiciones son aceptables para merge automático.
    """

    # Paths permitidos para auto-merge (solo estos)
    ALLOWED_PATHS = [
        "src/detectors/",
        "tests/",
        "docs/",
        "examples/",
        "README.md",
        "CHANGELOG.md",
        ".github/ISSUE_TEMPLATE/",
    ]

    # Paths SIEMPRE prohibidos (bloquean el merge aunque todo lo demás sea OK)
    FORBIDDEN_PATHS = [
        "src/core/",
        "src/utils/",
        ".github/workflows/",
        "scripts/",
        "requirements.txt",
        "pyproject.toml",
        "Makefile",
        "Dockerfile",
        ".gitignore",
    ]

    # Límites cuantitativos
    MAX_FILES = 10
    MAX_LINES_CHANGED = 500

    @classmethod
    def validate_paths(cls, changed_files: list[str]) -> tuple[bool, list[str]]:
        """
        Valida que todos los archivos modificados están en paths permitidos.

        Returns:
            (is_valid, list_of_violations)
        """
        violations = []

        for file_path in changed_files:
            # Verificar si está en paths prohibidos (prioridad máxima)
            is_forbidden = any(
                file_path.startswith(forbidden) or file_path == forbidden
                for forbidden in cls.FORBIDDEN_PATHS
            )
            if is_forbidden:
                violations.append(
                    f"🚫 PROHIBIDO: `{file_path}` (ruta crítica del sistema)"
                )
                continue

            # Verificar si está en paths permitidos
            is_allowed = any(
                file_path.startswith(allowed) or file_path == allowed
                for allowed in cls.ALLOWED_PATHS
            )
            if not is_allowed:
                violations.append(
                    f"❌ NO PERMITIDO: `{file_path}` "
                    f"(solo se permite modificar: {', '.join(cls.ALLOWED_PATHS)})"
                )

        return len(violations) == 0, violations

    @classmethod
    def validate_size(
        cls, num_files: int, lines_changed: int
    ) -> tuple[bool, list[str]]:
        """Valida que el PR no es demasiado grande."""
        violations = []

        if num_files > cls.MAX_FILES:
            violations.append(
                f"El PR modifica {num_files} archivos (máximo permitido: {cls.MAX_FILES})"
            )

        if lines_changed > cls.MAX_LINES_CHANGED:
            violations.append(
                f"El PR tiene {lines_changed} líneas cambiadas (máximo permitido: {cls.MAX_LINES_CHANGED})"
            )

        return len(violations) == 0, violations


class Scanner:
    """
    Motor principal de escaneo de PRs.
    """

    def __init__(self) -> None:
        self.detector_classes = discover_detectors()
        self.detectors = [cls() for cls in self.detector_classes]
        logger.info(
            f"Scanner inicializado con {len(self.detectors)} detectores: "
            f"{[d.name for d in self.detectors]}"
        )

    def scan_file(self, file_path: str, content: str) -> list[DetectorResult]:
        """Ejecuta todos los detectores sobre un archivo."""
        all_results = []

        for detector in self.detectors:
            try:
                if not detector.should_skip(file_path):
                    results = detector.analyze(file_path, content)
                    all_results.extend(results)
                    logger.debug(
                        f"  {detector.name}: {len(results)} findings en {file_path}"
                    )
            except Exception as e:
                logger.error(
                    f"Error en detector {detector.name} analizando {file_path}: {e}"
                )
                all_results.append(
                    DetectorResult(
                        status=DetectorStatus.WARNING,
                        detector_name=detector.name,
                        message=f"Error interno del detector: {str(e)}",
                        file_path=file_path,
                    )
                )

        return all_results

    def scan_pr(
        self,
        pr_number: int,
        changed_files: dict[str, str],  # {file_path: content}
        lines_changed: int = 0,
        skip_path_validation: bool = False,
    ) -> ScanResult:
        """
        Analiza todos los archivos de un PR y genera el resultado global.

        Args:
            pr_number: Número del PR en GitHub
            changed_files: Diccionario {ruta_archivo: contenido}
            lines_changed: Total de líneas modificadas
        """
        start_time = time.time()
        logger.info(f"🔍 Iniciando análisis del PR #{pr_number}")
        logger.info(f"   Archivos a analizar: {len(changed_files)}")

        all_findings = []

        # ── 1. Validación de paths (seguridad del sistema) ──
        path_ok, path_violations = SecurityRules.validate_paths(
            list(changed_files.keys())
        )
        size_ok, size_violations = SecurityRules.validate_size(
            len(changed_files), lines_changed
        )

        path_validation = {
            "paths_ok": path_ok or skip_path_validation,
            "size_ok": size_ok or skip_path_validation,
            "violations": path_violations + size_violations,
            "validation_skipped": skip_path_validation,
        }

        if skip_path_validation:
            logger.info("   🛠️ MANTENIMIENTO: Ignorando validación de paths/tamaño")

        if path_violations and not skip_path_validation:
            logger.warning(f"   ⚠️ Violaciones de paths: {path_violations}")

        # ── 2. Análisis de contenido con detectores ──
        for file_path, content in changed_files.items():
            logger.info(f"   Analizando: {file_path}")
            file_results = self.scan_file(file_path, content)

            if file_results:
                for r in file_results:
                    all_findings.append(r.to_dict())
                    level = r.status.value
                    logger.info(f"     [{level}] {r.detector_name}: {r.message}")

        # ── 3. Calcular métricas ──
        errors = sum(1 for f in all_findings if f["status"] == "ERROR")
        warnings = sum(1 for f in all_findings if f["status"] == "WARNING")
        ok_count = sum(1 for f in all_findings if f["status"] == "OK")

        # ── 4. Determinar estado global y decisión ──
        has_path_violations = (not path_ok or not size_ok) and not skip_path_validation

        if has_path_violations or errors > 0:
            global_status = "ERROR"
            decision = "REJECT"
        elif warnings > 0:
            global_status = "WARNING"
            decision = "WARN_MERGE"
        else:
            global_status = "OK"
            decision = "MERGE"

        duration_ms = (time.time() - start_time) * 1000

        result = ScanResult(
            global_status=global_status,
            decision=decision,
            pr_number=pr_number,
            files_analyzed=len(changed_files),
            total_findings=len(all_findings),
            errors=errors,
            warnings=warnings,
            ok_count=ok_count,
            findings=all_findings,
            scan_duration_ms=round(duration_ms, 2),
            detectors_run=[d.name for d in self.detectors],
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            path_validation=path_validation,
        )

        logger.info(f"✅ Análisis completado en {duration_ms:.0f}ms")
        logger.info(f"   Estado: {global_status} | Decisión: {decision}")
        logger.info(f"   Errores: {errors} | Advertencias: {warnings} | OK: {ok_count}")

        return result
