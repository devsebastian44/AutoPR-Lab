# 🤖 AutoPR Lab

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?style=flat&logo=github-actions&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=flat&logo=docker&logoColor=white)
![pre-commit](https://img.shields.io/badge/pre--commit-Enabled-FAB040?style=flat&logo=pre-commit&logoColor=black)
![Pytest](https://img.shields.io/badge/Testing-Pytest-0A9EDC?style=flat&logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-brightgreen?style=flat)

> **IMPORTANT:** This project is for educational and ethical cybersecurity purposes only.

---

## 🧠 Overview

**AutoPR Lab** es un sistema de **revisión y fusión automática de Pull Requests** construido sobre **GitHub Actions** y **Python 3.10+**. A partir del análisis de la estructura del repositorio, sus módulos fuente y archivos de configuración, el sistema intercepta cada PR abierto o actualizado en el repositorio, ejecuta una batería de detectores de seguridad modulares sobre el código propuesto, y toma una decisión trazable y autónoma — aprobar el merge, aprobar con advertencias o rechazar y cerrar el PR — sin intervención humana.

El motor de análisis (`core/scanner.py`) orquesta la ejecución de detectores independientes ubicados en `detectors/`, cada uno implementando un contrato común definido por `BaseDetector`. Los resultados son estandarizados mediante un dataclass `DetectorResult` que incluye estado, mensaje, detalles, ruta del archivo y número de línea. El motor de decisión (`scripts/decision_engine.py`) agrega los resultados, evalúa las reglas de seguridad de rutas (`SecurityRules`) y emite la decisión final a través de la GitHub REST API (`utils/github_api.py`), comentando automáticamente el PR y ejecutando la acción correspondiente.

Este proyecto es simultáneamente una herramienta funcional de automatización DevSecOps y un laboratorio de aprendizaje sobre arquitectura de sistemas de revisión de código, análisis estático y diseño de pipelines de CI/CD seguros.

---

## ⚙️ Features

- **Motor de decisión autónomo con tres estados** — Cada PR recibe una de tres decisiones: `MERGE` (sin problemas), `WARN_MERGE` (advertencias sin bloqueo) o `REJECT` (errores críticos), ejecutadas sin intervención humana.
- **Arquitectura de detectores modulares y extensibles** — Los detectores heredan de `BaseDetector` y retornan `DetectorResult` estandarizados. El sistema los autodescubre desde `detectors/__init__.py` sin modificar el motor principal.
- **Detección de secretos y credenciales** — `APIKeysDetector` identifica GitHub tokens, OpenAI API keys, AWS secrets, claves RSA y URLs con credenciales embebidas. `PasswordsDetector` detecta contraseñas hardcodeadas en variables de entorno y configuraciones.
- **Detección de archivos sensibles** — `SensitiveFilesDetector` bloquea PRs que incluyan `.env`, `.pem`, `.key`, `credentials.json` y archivos de base de datos.
- **Validación AST de nuevos detectores** — `DetectorFormatValidator` analiza la estructura sintáctica de nuevos detectores con `ast.parse()` antes de aceptarlos, bloqueando imports prohibidos (`subprocess`, `socket`, `requests`, `eval`, `exec`) y verificando la herencia correcta de `BaseDetector`.
- **Reglas estrictas de rutas y tamaño** — El sistema valida qué rutas son elegibles para auto-merge (detectores, tests, docs, examples) y bloquea permanentemente rutas críticas (core, workflows, scripts, dependencias). Límite de 10 archivos y 500 líneas por PR.
- **Comentarios automáticos del bot** — `utils/comment_templates.py` genera comentarios ricos y estructurados directamente sobre el PR explicando cada hallazgo con archivo, línea y severidad.
- **Modo DRY_RUN para pruebas locales** — Permite ejecutar el motor completo sin realizar acciones reales en la API de GitHub, ideal para desarrollo y testing del sistema.
- **Contenerización Docker** — `Dockerfile` y `.dockerignore` permiten ejecutar el sistema en un entorno aislado y reproducible.
- **Pre-commit hooks integrados** — `.pre-commit-config.yaml` garantiza calidad del código antes de cada commit en el repositorio.
- **Makefile para orquestación de tareas** — Comandos unificados para instalar, testear, lintear y ejecutar el sistema.

---

## 🛠️ Tech Stack

| Componente | Tecnología |
|---|---|
| Lenguaje principal | Python 3.10+ |
| Motor de CI/CD | GitHub Actions (`.github/workflows/`) |
| Análisis estático de código | `ast` (stdlib Python) |
| Cliente API | GitHub REST API v3 (`utils/github_api.py`) |
| Contenerización | Docker + `.dockerignore` |
| Pre-commit hooks | pre-commit framework |
| Testing | pytest |
| Build y orquestación | Makefile |
| Configuración del proyecto | pyproject.toml |
| Logging | Logger con colores (`utils/logger.py`) |
| Licencia | MIT |

---

## 📦 Installation

### Requisitos previos

- Python 3.10 o superior
- Docker (opcional, para ejecución contenerizada)
- Un repositorio en GitHub donde desplegar el sistema
- `GITHUB_TOKEN` con permisos de lectura/escritura sobre PRs

### Instalación local (desarrollo)

```bash
# 1. Clonar el repositorio
git clone https://github.com/devsebastian44/AutoPR-Lab.git
cd AutoPR-Lab

# 2. Crear entorno virtual e instalar dependencias
python3 -m venv venv
source venv/bin/activate       # Linux/macOS
venv\Scripts\activate          # Windows

pip install -r requirements.txt

# 3. Instalar pre-commit hooks
pre-commit install

# 4. Verificar instalación ejecutando los tests
make test
# o directamente:
python -m pytest tests/ -v
```

### Despliegue en repositorio propio (GitHub Actions)

```bash
# 1. Habilitar GitHub Actions en tu repositorio
# Settings → Actions → General

# 2. Configurar permisos del GITHUB_TOKEN
# Settings → Actions → General → Workflow permissions:
#   ✅ Read and write permissions
#   ✅ Allow GitHub Actions to create and approve pull requests

# 3. El workflow .github/workflows/auto-pr.yml
#    se activa automáticamente en cada PR. No requiere configuración adicional.
```

### Ejecución con Docker

```bash
# Construir la imagen
docker build -t autopr-lab .

# Ejecutar en modo DRY_RUN (sin acciones reales en GitHub)
docker run \
  -e GITHUB_TOKEN="tu_token" \
  -e GITHUB_REPOSITORY="owner/repo" \
  -e PR_NUMBER="123" \
  -e DRY_RUN="true" \
  autopr-lab
```

---

## ▶️ Usage

### Uso automático vía GitHub Actions

Una vez configurado, el sistema opera de forma completamente autónoma. Al abrir o actualizar cualquier PR en el repositorio, el workflow `auto-pr.yml` se dispara y ejecuta el pipeline completo:

```
PR Abierto / Actualizado
          │
          ▼
  [GitHub Actions Trigger]
  on: pull_request (opened, synchronize, reopened)
          │
          ▼
  [decision_engine.py]
  Lee GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER
  Obtiene lista de archivos del PR vía GitHub API
          │
          ▼
  [SecurityRules.validate_paths]
  ¿Archivos en rutas permitidas?
  ¿PR dentro de límites de tamaño?
          │
     ─────┴──────
     │           │
   PASS        FAIL
     │           │
     ▼        REJECT inmediato
  [Scanner.scan_pr]
  Ejecuta TODOS los detectores
  sobre cada archivo del PR
          │
     ─────┴──────────────
     │          │        │
   ERROR     WARNING    OK
     │          │        │
  REJECT   WARN_MERGE  MERGE
```

### Uso local / DRY_RUN

```bash
# 1. Copiar el archivo de entorno de ejemplo
cp .env.example .env

# 2. Configurar variables en .env (no requiere tokens reales si DRY_RUN=true)
# GITHUB_TOKEN="mock_token"
# DRY_RUN="true"

# 3. Ejecutar el motor de decisión
python scripts/decision_engine.py
```

### Comandos Makefile disponibles

```bash
make install    # Instala dependencias y pre-commit hooks
make test       # Ejecuta la suite completa de pytest
make lint       # Ejecuta linters sobre el código fuente
make run        # Ejecuta el motor en modo DRY_RUN
make docker     # Construye la imagen Docker
make clean      # Limpia artefactos de build y caché
```

### Salida del sistema — Ejemplos reales

**PR rechazado (credencial detectada):**
```
❌ [CRITICAL] APIKeysDetector: Posible OpenAI API Key detectada
   → Archivo: detectors/nuevo.py — Línea 5
   → Patrón: sk-ab****xyz (redactado)

❌ [CRITICAL] PasswordsDetector: Password hardcodeado en DATABASE_PASSWORD
   → Archivo: config.py — Línea 12

DECISIÓN FINAL: REJECT
→ Comentario publicado en PR #42
→ PR cerrado automáticamente
→ Tiempo total: 312ms
```

**PR aprobado y mergeado (detector limpio):**
```
✅ [OK] DetectorFormatValidator: Estructura del detector válida
✅ [OK] APIKeysDetector: Sin credenciales detectadas
✅ [OK] PasswordsDetector: Sin passwords hardcodeados
✅ [OK] SensitiveFilesDetector: Sin archivos sensibles

DECISIÓN FINAL: MERGE
→ PR #43 aprobado y mergeado automáticamente
→ Tiempo total: 89ms
```

---

## 📁 Project Structure

```
AutoPR-Lab/
│
├── .github/
│   └── workflows/
│       └── auto-pr.yml            # Workflow principal de GitHub Actions:
│                                  # trigger on PR, ejecuta decision_engine.py
│
├── core/
│   ├── __init__.py
│   └── scanner.py                 # Motor central de análisis:
│                                  # orquesta la ejecución de todos los
│                                  # detectores sobre los archivos del PR
│                                  # y agrega resultados DetectorResult
│
├── detectors/
│   ├── __init__.py                # Auto-descubrimiento de detectores:
│   │                              # registra automáticamente todos los
│   │                              # módulos del directorio
│   ├── base_detector.py           # Clase base abstracta BaseDetector:
│   │                              # contrato, DetectorResult dataclass,
│   │                              # DetectorStatus enum (OK/WARNING/ERROR)
│   ├── api_keys_detector.py       # Detecta tokens, API keys y secretos
│   │                              # (GitHub, OpenAI, AWS, RSA, URLs con creds)
│   ├── passwords_detector.py      # Detecta passwords hardcodeados y
│   │                              # contraseñas triviales en variables
│   ├── sensitive_files_detector.py# Detecta .env, .pem, .key, credentials.json
│   │                              # y archivos de base de datos en el PR
│   └── detector_validator.py      # Valida estructura AST de nuevos detectores:
│                                  # imports prohibidos, herencia BaseDetector,
│                                  # métodos requeridos (name, analyze)
│
├── utils/
│   ├── __init__.py
│   ├── github_api.py              # Cliente GitHub REST API v3:
│   │                              # obtiene archivos del PR, publica
│   │                              # comentarios, aprueba y ejecuta merge
│   ├── comment_templates.py       # Templates Markdown para comentarios
│   │                              # del bot: MERGE, WARN_MERGE, REJECT
│   └── logger.py                  # Sistema de logging con colores ANSI
│                                  # por nivel (INFO, WARNING, ERROR)
│
├── scripts/
│   └── decision_engine.py         # Entry point del sistema:
│                                  # lee variables de entorno, llama a
│                                  # SecurityRules + Scanner, emite decisión
│                                  # y ejecuta acción vía GitHub API
│
├── tests/
│   ├── test_detectors.py          # Tests unitarios de detectores:
│   │                              # casos positivos y negativos por detector
│   └── test_scanner.py            # Tests de integración del Scanner:
│                                  # flujo completo con mocks de GitHub API
│
├── docs/
│   ├── how-to-add-detector.md     # Guía paso a paso para agregar
│   │                              # nuevos detectores al sistema
│   └── example-outputs.md         # Ejemplos de outputs del bot
│                                  # en diferentes escenarios
│
├── examples/
│   ├── valid-pr/                  # Código de ejemplo que el sistema acepta
│   └── invalid-pr/                # Código de ejemplo que el sistema rechaza
│
├── .dockerignore                  # Exclusiones de imagen Docker
├── .gitignore                     # Exclusiones de Git
├── .pre-commit-config.yaml        # Configuración de pre-commit hooks
├── Dockerfile                     # Imagen Docker del sistema
├── LICENSE                        # Licencia MIT
├── Makefile                       # Comandos de orquestación del proyecto
├── pyproject.toml                 # Configuración del proyecto Python
                                   # (herramientas, linters, pytest)
└── requirements.txt               # Dependencias del proyecto
```

---

## 🔐 Security

El sistema está diseñado con un **modelo de seguridad por defecto estricto**. Toda decisión sigue el principio de mínimo privilegio: solo se permite lo que está explícitamente autorizado.

### Modelo de confianza de rutas

| Ruta | Estado | Razón |
|---|---|---|
| `detectors/` | ✅ Auto-merge | Extensiones del sistema, validadas por DetectorFormatValidator |
| `tests/` | ✅ Auto-merge | Pruebas unitarias, sin capacidad de ejecución en producción |
| `docs/` | ✅ Auto-merge | Solo documentación Markdown |
| `examples/` | ✅ Auto-merge | Código de demostración sin lógica productiva |
| `README.md` | ✅ Auto-merge | Documentación pública |
| `core/` | 🚫 Bloqueado | Motor principal — requiere revisión manual |
| `.github/workflows/` | 🚫 Bloqueado | Definición del pipeline CI/CD — crítico |
| `scripts/` | 🚫 Bloqueado | Motor de decisión — requiere revisión manual |
| `requirements.txt` | 🚫 Bloqueado | Modificar dependencias puede introducir supply chain attacks |
| `pyproject.toml` | 🚫 Bloqueado | Configuración del proyecto |
| `Makefile` | 🚫 Bloqueado | Automatización con acceso a shell |

### Validación AST de detectores entrantes

Antes de aceptar un nuevo detector, `DetectorFormatValidator` lo analiza con `ast.parse()` y bloquea:

```python
# Imports prohibidos — nunca aceptados en detectores:
FORBIDDEN_IMPORTS = [
    "subprocess",   # Ejecución de comandos del sistema
    "socket",       # Conexiones de red arbitrarias
    "requests",     # HTTP calls no autorizadas
    "os.system",    # Ejecución de shell commands
]

# Construcciones prohibidas:
FORBIDDEN_CONSTRUCTS = ["eval", "exec"]

# Requerimientos obligatorios:
REQUIRED_BASE_CLASS = "BaseDetector"
REQUIRED_METHODS = ["name", "description", "severity", "analyze"]
```

### Límites de tamaño por PR

- Máximo **10 archivos** modificados por PR
- Máximo **500 líneas** de cambios (adiciones + eliminaciones)
- PRs que excedan estos límites son rechazados automáticamente y marcados para revisión manual

### Modelo de permisos del GITHUB_TOKEN

  El sistema utiliza únicamente el `GITHUB_TOKEN` inyectado automáticamente por GitHub Actions, sin requerir tokens personales ni secrets adicionales. Los permisos mínimos requeridos son `pull-requests: write` y `contents: write`.

---

## 🤝 How to Contribute

¡Las contribuciones son bienvenidas! Este proyecto está diseñado para ser un laboratorio abierto y portafolio colaborativo donde otros desarrolladores pueden sumar detectores o mejorar el motor.

**Pasos para contribuir:**

1. **Haz un Fork** del repositorio a tu cuenta de GitHub.
2. **Clona** tu fork localmente y configura el entorno:

   ```bash
   git clone https://github.com/devsebastian44/AutoPR-Lab.git
   cd AutoPR-Lab
   pip install -e ".[dev,security]"
   cp .env.example .env
   ```

3. **Crea una rama** para tu funcionalidad o corrección (`git checkout -b feature/nuevo-detector`).
4. **Desarrolla y testea** localmente:
   - Asegúrate de agregar tests unitarios en `tests/` (sin usar credenciales reales, usa mocks).
   - Valida que todos los tests pasen usando `python -m pytest tests/`.
   - Verifica la calidad con `ruff check .` y `mypy .`.
5. **Haz Commit y Push** de tus cambios. Los pre-commit hooks integrados validarán tu código.
6. **Abre un Pull Request** hacia la rama `main` del repositorio original.
   - Nuestro CI workflow (`ci.yml`) validará automáticamente tus cambios (tests, linting, seguridad).
   - Nuestro motor AutoPR evaluará las reglas de seguridad de las rutas que modificaste.

---



## 🚀 Roadmap

Posibles extensiones identificadas desde la arquitectura modular del sistema:

- [ ] **Detector de dependencias vulnerables** — Integrar análisis de `requirements.txt` contra bases de datos de vulnerabilidades (PyPI Advisory Database, OSV) como nuevo detector modular.
- [ ] **Detector de complejidad ciclomática** — Rechazar automáticamente funciones con complejidad excesiva (CC > 10) usando la librería `radon`.
- [ ] **Dashboard de métricas** — Generar un reporte histórico de decisiones (tasa de rechazo, detectores más activos, tiempo medio de review) exportable como artefacto del workflow.
- [ ] **Configuración por repositorio** — Soporte para un archivo `.autopr.yml` en el repositorio raíz donde cada proyecto defina sus propias reglas de rutas, límites de tamaño y severidades.
- [ ] **Detector de cobertura de tests** — Verificar que los nuevos detectores incluyan tests unitarios antes de autorizar el merge automático.
- [ ] **Notificaciones por Slack/email** — Enviar resumen de decisiones a canales de notificación configurables cuando el bot ejecute acciones sobre PRs críticos.
- [ ] **Modo estricto por rama** — Aplicar reglas más restrictivas en PRs dirigidos a `main` vs `develop`, con políticas diferenciadas por rama destino.

---

## 📄 License

Este proyecto está bajo la licencia **MIT**.

```
MIT License — Copyright (c) Sebastian Zhunaula (devsebastian44)
Se permite el uso, copia, modificación y distribución con o sin
fines comerciales, siempre que se mantenga el aviso de copyright.
```

---

## 👨‍💻 Author

**Sebastian Zhunaula**
[GitHub: @devsebastian44](https://github.com/devsebastian44)

> Sistema desarrollado como laboratorio de automatización DevSecOps,
> explorando patrones de arquitectura modular, análisis estático de código
> y diseño de pipelines de CI/CD seguros sobre GitHub Actions.