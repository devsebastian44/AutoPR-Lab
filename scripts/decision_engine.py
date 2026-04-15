#!/usr/bin/env python3
"""
AutoPR Lab - Decision Engine
==============================
Script principal invocado por GitHub Actions.
Orquesta el análisis completo y ejecuta la decisión automática.

Uso:
    python scripts/decision_engine.py

Variables de entorno requeridas:
    GITHUB_TOKEN    - Token del workflow de GitHub Actions
    GITHUB_REPO     - Repositorio en formato "owner/repo"
    PR_NUMBER       - Número del Pull Request
    PR_BASE_BRANCH  - Branch destino del PR (opcional, default: main)

Variables opcionales:
    DRY_RUN         - Si es "true", no ejecuta acciones (solo analiza)
    LOG_LEVEL       - Nivel de logging (DEBUG, INFO, WARNING, ERROR)
"""

import json
import os
import sys

# Agregar el directorio raíz y src al path para imports
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "src"))

from core.scanner import Scanner, ScanResult  # noqa: E402
from utils.comment_templates import (  # noqa: E402
    build_merge_comment,
    build_reject_comment,
    build_warn_merge_comment,
)
from utils.github_api import GitHubAPI, GitHubAPIError  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("decision_engine")


def get_required_env(name: str) -> str:
    """Obtiene una variable de entorno requerida o termina con error."""
    value = os.environ.get(name, "").strip()
    if not value:
        logger.error(f"Variable de entorno requerida no encontrada: {name}")
        sys.exit(1)
    return value


def collect_pr_files(github: GitHubAPI) -> tuple[dict[str, str], int]:
    """
    Descarga los archivos modificados del PR.
    Intenta obtener el contenido completo de cada archivo.

    Returns:
        ({file_path: content}, total_lines_changed)
    """
    logger.info("📥 Descargando archivos del PR...")
    pr_info = github.get_pr_info()
    head_sha = pr_info.get("head", {}).get("sha", "")
    changed_files_info = github.get_changed_files()

    changed_files = {}
    total_lines = 0

    for file_info in changed_files_info:
        file_path = file_info.get("filename", "")
        additions = file_info.get("additions", 0)
        deletions = file_info.get("deletions", 0)
        total_lines += additions + deletions

        raw_url = file_info.get("raw_url", "")
        status = file_info.get("status", "")

        # Si el archivo fue eliminado, usar string vacío para el análisis
        if status == "removed":
            changed_files[file_path] = ""
            logger.info(f"   📄 {file_path} (eliminado)")
            continue

        # Descargar contenido completo
        content = ""
        if raw_url:
            content = github.get_file_content(raw_url)

        # Fallback: si raw_url falló o no existe, intentar por API de contenidos
        if not content and head_sha:
            logger.debug(f"   ⚠️ Usando fallback para {file_path}")
            content = github.get_file_content_by_path(file_path, head_sha)

        # Último recurso: usar el patch (no recomendado por ser incompleto)
        if not content:
            patch = file_info.get("patch", "")
            if patch:
                logger.warning(
                    f"   ⚠️ Escaneando solo el fragmento (patch) de {file_path}"
                )
                content = patch

        changed_files[file_path] = content
        logger.info(f"   📄 {file_path} (+{additions}/-{deletions})")

    logger.info(
        f"   Total: {len(changed_files)} archivos, {total_lines} líneas cambiadas"
    )
    return changed_files, total_lines


def execute_decision(
    github: GitHubAPI,
    result: ScanResult,
    dry_run: bool = False,
) -> int:
    """
    Ejecuta la decisión basada en el resultado del análisis.

    Returns:
        Exit code: 0 = éxito, 1 = PR rechazado, 2 = error
    """
    decision = result.decision
    pr_number = result.pr_number

    logger.info("")
    logger.info(f"{'=' * 60}")
    logger.info(f"  DECISIÓN FINAL: {decision}")
    logger.info(f"{'=' * 60}")
    logger.info(f"  PR #{pr_number}")
    logger.info(f"  Estado: {result.global_status}")
    logger.info(f"  Errores: {result.errors} | Advertencias: {result.warnings}")
    logger.info(f"{'=' * 60}")
    logger.info("")

    if dry_run:
        logger.info("🔍 DRY RUN activado — No se ejecutarán acciones reales")
        logger.info(f"   Decisión que se tomaría: {decision}")
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0

    try:
        if decision == "MERGE":
            # ── PR Limpio: Aprobar + Merge ──────────────────────────────
            logger.info("✅ Ejecutando: APPROVE + MERGE")

            github.approve_pr(
                "AutoPR Lab: ✅ Análisis de seguridad completado sin problemas."
            )
            github.merge_pr(
                commit_title=f"[AutoPR] Merge PR #{pr_number} (auto-approved)",
                commit_message=(
                    f"AutoPR Lab: Merge automático del PR #{pr_number}\n\n"
                    f"Detectores ejecutados: {len(result.detectors_run)}\n"
                    f"Archivos analizados: {result.files_analyzed}\n"
                    f"Resultado: {result.global_status}"
                ),
                merge_method="squash",
            )
            github.add_comment(build_merge_comment(result))
            logger.info("✅ PR mergeado exitosamente")
            return 0

        elif decision == "WARN_MERGE":
            # ── PR con Advertencias: Aprobar + Merge + Comentario ───────
            logger.info("⚠️  Ejecutando: APPROVE + MERGE (con advertencias)")

            github.approve_pr(
                f"AutoPR Lab: ⚠️ Aprobado con {result.warnings} advertencia(s). "
                "Ver comentario para detalles."
            )
            github.merge_pr(
                commit_title=f"[AutoPR] Merge PR #{pr_number} (warnings)",
                merge_method="squash",
            )
            github.add_comment(build_warn_merge_comment(result))
            logger.info("⚠️  PR mergeado con advertencias")
            return 0

        elif decision == "REJECT":
            # ── PR con Errores: Comentar + Cerrar ───────────────────────
            logger.info("❌ Ejecutando: COMMENT + CLOSE")

            github.add_comment(build_reject_comment(result))
            github.close_pr()
            logger.info("❌ PR rechazado y cerrado")

            # Salir con código de error para que el workflow falle
            return 1

        else:
            logger.error(f"Decisión desconocida: {decision}")
            return 2

    except GitHubAPIError as e:
        logger.error(f"Error de GitHub API: {e}")
        logger.error(f"  Status code: {e.status_code}")
        logger.error(f"  Respuesta: {e.response[:200]}")
        return 2


def main() -> int:
    """Función principal del decision engine."""
    logger.info("")
    logger.info("🚀 AutoPR Lab — Decision Engine v1.0")
    logger.info("=" * 50)

    # ── Configuración ──────────────────────────────────────────────────
    token = get_required_env("GITHUB_TOKEN")
    repo = get_required_env("GITHUB_REPOSITORY")
    pr_number_str = get_required_env("PR_NUMBER")
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

    try:
        pr_number = int(pr_number_str)
    except ValueError:
        logger.error(f"PR_NUMBER inválido: '{pr_number_str}'")
        sys.exit(1)

    logger.info(f"  Repositorio: {repo}")
    logger.info(f"  PR: #{pr_number}")
    logger.info(f"  Dry Run: {dry_run}")
    logger.info("")

    # ── GitHub API ─────────────────────────────────────────────────────
    github = GitHubAPI(token=token, repo=repo, pr_number=pr_number)

    # ── Descargar archivos del PR ───────────────────────────────────────
    try:
        changed_files, total_lines = collect_pr_files(github)
    except GitHubAPIError as e:
        logger.error(f"No se pudieron obtener los archivos del PR: {e}")
        sys.exit(2)

    if not changed_files:
        logger.warning("El PR no tiene archivos modificados detectables")
        sys.exit(0)

    # ── Análisis con Scanner ───────────────────────────────────────────
    # Detectar si el PR tiene etiquetas de mantenimiento para bypass de seguridad
    pr_labels = [
        label.get("name", "") for label in github.get_pr_info().get("labels", [])
    ]
    is_maintenance = any(
        name in ["maintenance", "system-upgrade"] for name in pr_labels
    )

    scanner = Scanner()
    result = scanner.scan_pr(
        pr_number=pr_number,
        changed_files=changed_files,
        lines_changed=total_lines,
        skip_path_validation=is_maintenance,
    )

    # ── Guardar resultado como artefacto ───────────────────────────────
    output_path = os.environ.get("SCAN_OUTPUT", "scan_result.json")
    with open(output_path, "w") as f:
        f.write(result.to_json())
    logger.info(f"📄 Resultado guardado en: {output_path}")

    # Exportar para GitHub Actions outputs
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"decision={result.decision}\n")
            f.write(f"status={result.global_status}\n")
            f.write(f"errors={result.errors}\n")
            f.write(f"warnings={result.warnings}\n")

    # ── Ejecutar decisión ──────────────────────────────────────────────
    exit_code = execute_decision(github, result, dry_run=dry_run)

    logger.info("")
    logger.info(f"AutoPR Lab finalizado con código: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
