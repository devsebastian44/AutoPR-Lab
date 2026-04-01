"""
AutoPR Lab - Comment Templates
================================
Plantillas para los comentarios automáticos del bot en PRs.
"""

from typing import Any


def _findings_section(findings: list[dict[str, Any]]) -> str:
    """Genera la sección de hallazgos agrupados por estado."""
    if not findings:
        return "_No se encontraron problemas._\n"

    errors = [f for f in findings if f["status"] == "ERROR"]
    warnings = [f for f in findings if f["status"] == "WARNING"]

    lines = []

    if errors:
        lines.append("**❌ Errores críticos:**")
        for f in errors:
            loc = f"en `{f['file_path']}`" if f.get("file_path") else ""
            line_ref = f", línea {f['line_number']}" if f.get("line_number") else ""
            lines.append(f"- **{f['detector_name']}**: {f['message']} {loc}{line_ref}")
            for detail in f.get("details", []):
                lines.append(f"  - {detail}")
        lines.append("")

    if warnings:
        lines.append("**⚠️ Advertencias:**")
        for f in warnings:
            loc = f"en `{f['file_path']}`" if f.get("file_path") else ""
            lines.append(f"- **{f['detector_name']}**: {f['message']} {loc}")
            for detail in f.get("details", []):
                lines.append(f"  - {detail}")
        lines.append("")

    return "\n".join(lines)


def _path_violations_section(path_validation: dict[str, Any]) -> str:
    """Genera la sección de violaciones de paths."""
    violations = path_validation.get("violations", [])
    if not violations:
        return ""

    lines = ["**🛡️ Violaciones de reglas de seguridad:**"]
    for v in violations:
        lines.append(f"- {v}")
    lines.append("")
    return "\n".join(lines)


def build_merge_comment(result: Any) -> str:
    """Comentario cuando el PR es mergeado exitosamente."""
    return f"""## 🤖 AutoPR Lab — Análisis Completado

### ✅ DECISIÓN: MERGE AUTOMÁTICO APROBADO

El PR cumple todos los requisitos de seguridad y calidad.

---

### 📊 Resumen del Análisis

| Métrica | Valor |
|---------|-------|
| Archivos analizados | `{result.files_analyzed}` |
| Detectores ejecutados | `{len(result.detectors_run)}` |
| Errores | `0` |
| Advertencias | `0` |
| Tiempo de análisis | `{result.scan_duration_ms:.0f}ms` |

### 🔍 Detectores ejecutados
{chr(10).join(f"- ✅ `{d}`" for d in result.detectors_run)}

---

> 🔀 **Este PR ha sido mergeado automáticamente** por AutoPR Lab.
> _Análisis completado: {result.timestamp}_
"""


def build_warn_merge_comment(result: Any) -> str:
    """Comentario cuando el PR es mergeado con advertencias."""
    findings_text = _findings_section(result.findings)

    return f"""## 🤖 AutoPR Lab — Análisis Completado

### ⚠️ DECISIÓN: MERGE CON ADVERTENCIAS

El PR fue mergeado automáticamente pero se detectaron advertencias no críticas.

---

### 📊 Resumen del Análisis

| Métrica | Valor |
|---------|-------|
| Archivos analizados | `{result.files_analyzed}` |
| Errores | `0` ✅ |
| Advertencias | `{result.warnings}` ⚠️ |
| Tiempo de análisis | `{result.scan_duration_ms:.0f}ms` |

### ⚠️ Hallazgos (no críticos)

{findings_text}

### ℹ️ Nota
Las advertencias no bloquean el merge pero se recomienda revisarlas en el futuro.

---

> 🔀 **Este PR ha sido mergeado automáticamente** a pesar de las advertencias.
> _Análisis completado: {result.timestamp}_
"""


def build_reject_comment(result: Any) -> str:
    """Comentario cuando el PR es rechazado."""
    findings_text = _findings_section(result.findings)
    path_text = _path_violations_section(result.path_validation)

    reasons_list = []
    if result.errors > 0:
        reasons_list.append(
            f"Se encontraron **{result.errors} error(es) crítico(s)** en el análisis de seguridad"
        )
    if not result.path_validation.get("paths_ok", True):
        reasons_list.append(
            "El PR modifica **archivos o rutas no permitidas** para auto-merge"
        )
    if not result.path_validation.get("size_ok", True):
        reasons_list.append(
            "El PR **excede los límites de tamaño** permitidos para auto-merge"
        )

    reasons_text = "\n".join(f"- {r}" for r in reasons_list)

    return f"""## 🤖 AutoPR Lab — Análisis Completado

### ❌ DECISIÓN: PR RECHAZADO Y CERRADO

Este PR ha sido cerrado automáticamente por las siguientes razones:

{reasons_text}

---

### 📊 Resumen del Análisis

| Métrica | Valor |
|---------|-------|
| Archivos analizados | `{result.files_analyzed}` |
| Errores críticos | `{result.errors}` ❌ |
| Advertencias | `{result.warnings}` ⚠️ |
| Tiempo de análisis | `{result.scan_duration_ms:.0f}ms` |

---

{path_text}

### 🔍 Problemas Detectados

{findings_text}

---

### 🔧 ¿Cómo corregir este PR?

1. **Revisa los errores listados** y corrígelos en tu branch
2. **Asegúrate de que los archivos modificados** solo estén en rutas permitidas:
   - ✅ `/detectors/` — Para agregar nuevos detectores
   - ✅ `/tests/` — Para tests
   - ✅ `/docs/` — Para documentación
3. **Nunca incluyas** API keys, passwords o archivos sensibles en el código
4. **Abre un nuevo PR** una vez corregidos los problemas
5. Para cambios en `/core/` o workflows, [abre un issue](../../issues/new) para revisión manual

---

> 🚫 **Este PR ha sido cerrado automáticamente** por AutoPR Lab.
> _Para apelar esta decisión, contacta a los maintainers del proyecto._
> _Análisis completado: {result.timestamp}_
"""
