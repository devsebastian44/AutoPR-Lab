# 📊 Ejemplos de Outputs de AutoPR Lab

Esta página muestra los outputs reales del sistema en distintos escenarios.

---

## Escenario 1: PR Limpio → MERGE ✅

**PR:** Agrega `SQLInjectionDetector` con tests

```
INFO     autopr.scanner | 🔍 Iniciando análisis del PR #42
INFO     autopr.scanner |    Archivos a analizar: 2
INFO     autopr.scanner |    Analizando: detectors/sql_injection_detector.py
INFO     autopr.scanner |      [OK] DetectorFormatValidator: Estructura del detector válida
INFO     autopr.scanner |    Analizando: tests/test_sql_injection_detector.py
INFO     autopr.scanner | ✅ Análisis completado en 87ms
INFO     autopr.scanner |    Estado: OK | Decisión: MERGE
INFO     autopr.scanner |    Errores: 0 | Advertencias: 0 | OK: 2
```

**Comentario en el PR:**

---

## 🤖 AutoPR Lab — Análisis Completado

### ✅ DECISIÓN: MERGE AUTOMÁTICO APROBADO

El PR cumple todos los requisitos de seguridad y calidad.

| Métrica | Valor |
|---------|-------|
| Archivos analizados | `2` |
| Detectores ejecutados | `4` |
| Errores | `0` |
| Advertencias | `0` |
| Tiempo de análisis | `87ms` |

### 🔍 Detectores ejecutados
- ✅ `APIKeysDetector`
- ✅ `PasswordsDetector`
- ✅ `SensitiveFilesDetector`
- ✅ `DetectorFormatValidator`

> 🔀 **Este PR ha sido mergeado automáticamente** por AutoPR Lab.

---

## Escenario 2: PR con Advertencias → WARN_MERGE ⚠️

**PR:** Agrega detector con archivo `.env.example` (template)

```
INFO     autopr.scanner | 🔍 Iniciando análisis del PR #43
INFO     autopr.scanner |    Archivos a analizar: 2
INFO     autopr.scanner |    Analizando: detectors/new_detector.py
INFO     autopr.scanner |      [OK] DetectorFormatValidator: Estructura del detector válida
INFO     autopr.scanner |    Analizando: .env.example
INFO     autopr.scanner |      [WARNING] SensitiveFilesDetector: Archivo de template detectado
INFO     autopr.scanner | ✅ Análisis completado en 102ms
INFO     autopr.scanner |    Estado: WARNING | Decisión: WARN_MERGE
INFO     autopr.scanner |    Errores: 0 | Advertencias: 1 | OK: 1
```

**Comentario en el PR:**

---

## 🤖 AutoPR Lab — Análisis Completado

### ⚠️ DECISIÓN: MERGE CON ADVERTENCIAS

**⚠️ Advertencias:**
- **SensitiveFilesDetector**: Archivo de template detectado: `.env.example` en `.env.example`
  - Este archivo de ejemplo/template es aceptable si solo contiene placeholders.
  - ✅ Asegúrate de que los valores sean ficticios (ej: YOUR_API_KEY_HERE).

> 🔀 **Este PR ha sido mergeado automáticamente** a pesar de las advertencias.

---

## Escenario 3: PR con Errores → REJECT ❌

**PR:** Intenta agregar un detector con API key hardcodeada

```
INFO     autopr.scanner | 🔍 Iniciando análisis del PR #44
INFO     autopr.scanner |    Archivos a analizar: 1
INFO     autopr.scanner |    Analizando: detectors/malicious_detector.py
INFO     autopr.scanner |      [ERROR] APIKeysDetector: Posible OpenAI API Key detectado
INFO     autopr.scanner |      [ERROR] PasswordsDetector: Password hardcodeado en 'DATABASE_PASSWORD'
INFO     autopr.scanner |      [ERROR] DetectorFormatValidator: Import prohibido: subprocess
INFO     autopr.scanner |      [ERROR] DetectorFormatValidator: Función peligrosa: eval()
INFO     autopr.scanner |      [ERROR] SensitiveFilesDetector: Clave privada RSA detectada
WARNING  autopr.scanner |    ⚠️ Violaciones de paths: []
INFO     autopr.scanner | ✅ Análisis completado en 134ms
INFO     autopr.scanner |    Estado: ERROR | Decisión: REJECT
INFO     autopr.scanner |    Errores: 5 | Advertencias: 0 | OK: 0
```

**Comentario en el PR:**

---

## 🤖 AutoPR Lab — Análisis Completado

### ❌ DECISIÓN: PR RECHAZADO Y CERRADO

**❌ Errores críticos:**
- **APIKeysDetector**: Posible OpenAI API Key detectado en `detectors/malicious_detector.py`, línea 14
  - Patrón detectado: `sk-ab****************************ijk`
  - ⚠️ Nunca hardcodees credenciales. Usa variables de entorno.
- **PasswordsDetector**: Password hardcodeado en variable 'DATABASE_PASSWORD'
  - Variable: `DATABASE_PASSWORD`
- **DetectorFormatValidator**: Import prohibido en detector: `subprocess`
  - Los detectores no pueden importar módulos de red o ejecución de código.
- **DetectorFormatValidator**: Función peligrosa en detector: `eval()`
  - `eval()` puede ejecutar código arbitrario y está prohibida en detectores.
- **SensitiveFilesDetector**: Contenido sensible: Clave privada PEM

> 🚫 **Este PR ha sido cerrado automáticamente** por AutoPR Lab.

---

## Escenario 4: Modificación de /core/ → REJECT ❌

**PR:** Intenta modificar `core/scanner.py` (ruta prohibida)

```
INFO     autopr.scanner | 🔍 Iniciando análisis del PR #45
WARNING  autopr.scanner |    ⚠️ Violaciones de paths:
WARNING  autopr.scanner |      🚫 PROHIBIDO: core/scanner.py (ruta crítica del sistema)
INFO     autopr.scanner | ✅ Análisis completado en 12ms
INFO     autopr.scanner |    Estado: ERROR | Decisión: REJECT
```

**Comentario en el PR:**

---

**🛡️ Violaciones de reglas de seguridad:**
- 🚫 PROHIBIDO: `core/scanner.py` (ruta crítica del sistema)

### 🔧 ¿Cómo corregir este PR?
1. Los archivos modificados deben estar solo en: `/detectors/`, `/tests/`, `/docs/`
2. Para cambios en `/core/` o workflows, abre un issue para revisión manual.

---

## Scan Result JSON (ejemplo)

```json
{
  "global_status": "ERROR",
  "decision": "REJECT",
  "pr_number": 44,
  "files_analyzed": 1,
  "total_findings": 5,
  "errors": 5,
  "warnings": 0,
  "ok_count": 0,
  "scan_duration_ms": 134.7,
  "detectors_run": [
    "APIKeysDetector",
    "PasswordsDetector",
    "SensitiveFilesDetector",
    "DetectorFormatValidator"
  ],
  "timestamp": "2025-03-15T10:30:00Z",
  "path_validation": {
    "paths_ok": true,
    "size_ok": true,
    "violations": []
  },
  "findings": [
    {
      "status": "ERROR",
      "detector_name": "APIKeysDetector",
      "message": "Posible OpenAI API Key detectado",
      "details": [
        "Patrón detectado: `sk-ab****************************ijk`",
        "⚠️ Nunca hardcodees credenciales. Usa variables de entorno."
      ],
      "file_path": "detectors/malicious_detector.py",
      "line_number": 14
    }
  ]
}
```
