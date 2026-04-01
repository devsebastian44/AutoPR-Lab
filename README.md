# 🤖 AutoPR Lab

> **Sistema de revisión y merge automático de Pull Requests con análisis de seguridad integrado.**  
> Cero intervención humana. Reglas estrictas. Decisiones trazables.

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Security: Automated](https://img.shields.io/badge/Security-Automated-red)](docs/security.md)

---

## ¿Qué es AutoPR Lab?

AutoPR Lab es un sistema de **revisión automática de Pull Requests** construido sobre GitHub Actions y Python. Analiza cada PR en tiempo real, ejecuta detectores de seguridad modulares, y toma una de tres decisiones sin intervención humana:

| Decisión | Condición | Acción |
|----------|-----------|--------|
| ✅ **MERGE** | Sin problemas | Aprueba + merge automático |
| ⚠️ **WARN MERGE** | Solo advertencias | Aprueba + merge + comentario |
| ❌ **REJECT** | Errores críticos | Comenta problemas + cierra PR |

---

## 🏗️ Arquitectura del Proyecto

```
AutoPR-Lab/
│
├── .github/
│   └── workflows/
│       └── auto-pr.yml          # Workflow principal de GitHub Actions
│
├── core/
│   ├── __init__.py
│   └── scanner.py               # Motor principal de análisis
│
├── detectors/
│   ├── __init__.py              # Auto-descubrimiento de detectores
│   ├── base_detector.py         # Clase base abstracta (contrato)
│   ├── api_keys_detector.py     # Detecta API keys y tokens
│   ├── passwords_detector.py    # Detecta passwords hardcodeados
│   ├── sensitive_files_detector.py  # Detecta archivos sensibles
│   └── detector_validator.py    # Valida estructura de detectores nuevos
│
├── utils/
│   ├── __init__.py
│   ├── github_api.py            # Cliente de la GitHub REST API
│   ├── comment_templates.py     # Templates para comentarios del bot
│   └── logger.py                # Sistema de logging con colores
│
├── scripts/
│   └── decision_engine.py       # Entry point: orquesta todo el flujo
│
├── tests/
│   ├── test_detectors.py        # Tests unitarios de detectores
│   └── test_scanner.py          # Tests de integración del scanner
│
├── docs/
│   ├── how-to-add-detector.md   # Guía para contributors
│   └── example-outputs.md       # Ejemplos de outputs del sistema
│
├── examples/
│   ├── valid-pr/                # Ejemplos de PRs que serán aceptados
│   └── invalid-pr/              # Ejemplos de PRs que serán rechazados
│
└── requirements.txt             # Dependencias (solo stdlib de Python)
```

---

## 🔍 Sistema de Detectores

Los detectores son módulos **independientes** que analizan el código y devuelven resultados estandarizados:

```python
@dataclass
class DetectorResult:
    status: DetectorStatus      # OK | WARNING | ERROR
    detector_name: str
    message: str
    details: List[str]
    file_path: Optional[str]
    line_number: Optional[int]
```

### Detectores incluidos

| Detector | Qué detecta | Severidad |
|----------|-------------|-----------|
| `APIKeysDetector` | GitHub tokens, OpenAI keys, AWS secrets, claves RSA, URLs con credenciales | 🔴 Critical |
| `PasswordsDetector` | Passwords hardcodeados, contraseñas triviales, tokens de autenticación | 🔴 Critical |
| `SensitiveFilesDetector` | `.env`, `.pem`, `.key`, `credentials.json`, archivos de BD | 🔴 Critical |
| `DetectorFormatValidator` | Estructura, imports prohibidos, `eval/exec`, herencia correcta | 🔴 Critical |

---

## 🛡️ Reglas de Seguridad (Auto-Merge)

El sistema solo permite merge automático cuando se cumplen **TODAS** estas condiciones:

### ✅ Rutas permitidas para auto-merge
```
detectors/     ← Nuevos detectores
tests/         ← Tests
docs/          ← Documentación
examples/      ← Ejemplos
README.md      ← Readme principal
```

### 🚫 Rutas siempre bloqueadas
```
core/                    ← Motor principal (requiere revisión manual)
.github/workflows/       ← Workflows de CI/CD (crítico)
scripts/                 ← Scripts de decisión
requirements.txt         ← Dependencias
pyproject.toml           ← Configuración del proyecto
Makefile                 ← Automatización
```

### 📏 Límites de tamaño
- Máximo **10 archivos** por PR
- Máximo **500 líneas** cambiadas

---

## ⚡ Cómo Funciona (Flujo Completo)

```
PR Abierto/Actualizado
        │
        ▼
┌─────────────────────────────────┐
│   GitHub Actions Trigger        │
│   on: pull_request              │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   decision_engine.py            │
│   - Lee variables de entorno    │
│   - Obtiene archivos del PR     │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   SecurityRules.validate_paths  │
│   - ¿Rutas permitidas?          │
│   - ¿Tamaño dentro de límites?  │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   Scanner.scan_pr               │
│   - Ejecuta TODOS los           │
│     detectores sobre cada       │
│     archivo del PR              │
└─────────────┬───────────────────┘
              │
    ┌─────────┼──────────┐
    ▼         ▼          ▼
  ERROR    WARNING      OK
    │         │          │
    ▼         ▼          ▼
 REJECT  WARN_MERGE    MERGE
    │         │          │
    ▼         ▼          ▼
Comentar  Aprobar    Aprobar
 + Cerrar + Merge    + Merge
           + Comentar
```

---

## 🚀 Instalación y Configuración

### 1. Fork o clona el repositorio

```bash
git clone https://github.com/devsebastian44/AutoPR-Lab.git
cd AutoPR-Lab
```

### 2. Habilitar GitHub Actions

El workflow en `.github/workflows/auto-pr.yml` se activa automáticamente en cada PR.

**No necesitas configurar nada adicional** — usa el `GITHUB_TOKEN` que GitHub provee automáticamente.

### 3. Configurar permisos del repositorio

En `Settings → Actions → General`:
- Marcar **"Read and write permissions"** para el GITHUB_TOKEN
- Marcar **"Allow GitHub Actions to create and approve pull requests"**

### 4. Opcional: Ejecutar localmente

```bash
# Instalar dependencias (solo para desarrollo)
pip install -r requirements.txt

# Ejecutar tests
python -m pytest tests/ -v

# Dry run (sin ejecutar acciones reales en GitHub)
export GITHUB_TOKEN="tu_token"
export GITHUB_REPOSITORY="owner/repo"
export PR_NUMBER="123"
export DRY_RUN="true"
python scripts/decision_engine.py
```

---

## 🔌 Agregar un Detector Nuevo

1. Crea `/detectors/mi_detector.py` heredando de `BaseDetector`
2. Crea `/tests/test_mi_detector.py` con tests unitarios
3. Abre un PR — **AutoPR Lab lo revisará y mergeará automáticamente** si está bien formado

```python
# detectors/mi_detector.py
from detectors.base_detector import BaseDetector, DetectorResult, DetectorStatus
from typing import List

class MiDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "MiDetector"

    @property
    def description(self) -> str:
        return "Detecta X en el código"

    @property
    def severity(self) -> str:
        return "high"  # critical | high | medium | low

    def analyze(self, file_path: str, content: str) -> List[DetectorResult]:
        results = []
        # Tu lógica aquí...
        return results
```

Ver guía completa: [docs/how-to-add-detector.md](docs/how-to-add-detector.md)

---

## 📊 Ejemplo de Output

### PR Rechazado (con API key)

```
❌ [ERROR] APIKeysDetector: Posible OpenAI API Key detectado
    - Patrón detectado: sk-ab****ijk (detectors/bad.py, línea 5)
    
❌ [ERROR] PasswordsDetector: Password hardcodeado en 'DATABASE_PASSWORD'
    - Variable: DATABASE_PASSWORD (config.py, línea 12)

DECISIÓN: REJECT
→ PR comentado y cerrado automáticamente
```

### PR Aprobado (detector limpio)

```
✅ [OK] DetectorFormatValidator: Estructura del detector válida
✅ [OK] APIKeysDetector: Sin credenciales detectadas
✅ [OK] PasswordsDetector: Sin passwords hardcodeados
✅ [OK] SensitiveFilesDetector: Sin archivos sensibles

DECISIÓN: MERGE
→ PR aprobado y mergeado automáticamente en 89ms
```

Ver más ejemplos: [docs/example-outputs.md](docs/example-outputs.md)

---

## 🔒 Modelo de Seguridad

### Protección contra abuso
- **Validación de paths**: Solo archivos en rutas explícitamente permitidas
- **Análisis estático de AST**: Los detectores nuevos son analizados con `ast.parse()` antes de ser aceptados
- **Imports prohibidos**: `subprocess`, `socket`, `requests`, `eval`, `exec` son bloqueados automáticamente
- **Límites de tamaño**: PRs grandes requieren revisión manual
- **Sin ejecución de código**: Los detectores NUNCA ejecutan el código que analizan, solo lo leen como texto

### Qué requiere revisión manual
Cualquier cambio en estas áreas **nunca se auto-mergea**:
- El motor de decisión (`src/core/`, `scripts/`)
- Los workflows de GitHub Actions
- Las dependencias del proyecto

---

## 🏛️ Arquitectura DevSecOps (GitLab vs GitHub)

Para mantener los estándares más altos de seguridad profesional, **AutoPR-Lab** utiliza una arquitectura de repositorio dual.

1. **GitLab (Laboratorio Privado)**: Actúa como el *Source of Truth*. Contiene todo el código núcleo (`src/core`), tests exhaustivos de vulnerabilidades, pipelines de Integración Continua (`.gitlab-ci.yml`) y scripts de publicación de automatización privada. Aquí es donde se realiza todo el desarrollo y de donde se extraen las métricas.
2. **GitHub (Portafolio Público)**: Es un entorno estrictamente *sanitizado*. Sirve como muestra pública, portafolio y demostración de arquitectura. Las partes críticas de análisis, tests ofensivos/defensivos y flujos de automatización privada son extraídas sistemáticamente.

### 🔄 Flujo de Publicación (publish_public.ps1)

El script `./scripts/publish_public.ps1` garantiza que nunca se filtren componentes sensibles del laboratorio al portafolio.
Ejecuta el siguiente pipeline seguro:
1. Validar el estado limpio de la rama `main` y sincronizar contra GitLab.
2. Crear un entorno en una rama de publicación aislada temporal.
3. Ejecutar `git rm` estructurado para borrar toda la ruta de tests, configuraciones, infraestructura de despliegue interno y lógica pesada.
4. Efectuar un un force-push de la versión higienizada a GitHub origin.
5. Devolver al desarrollador intacto al entorno del Laboratorio Privado.

Puedes consultar el diagrama detallado del flujo en [diagrams/architecture.md](diagrams/architecture.md).
