# 🔌 Cómo Agregar un Detector a AutoPR Lab

Esta guía explica paso a paso cómo contribuir con un detector nuevo al sistema.

## 📋 Requisitos previos

- Python 3.10+
- Conocimiento básico de `re` (regex) y `ast` (AST de Python)
- Haber leído el código de un detector existente (ej: `api_keys_detector.py`)

---

## 1. Crear el archivo del detector

Crea un nuevo archivo en `/detectors/`:

```
detectors/
└── mi_nuevo_detector.py   ← Tu archivo aquí
```

**Regla de naming:** `nombre_detector.py` en snake_case.

---

## 2. Estructura mínima requerida

Todo detector **debe** heredar de `BaseDetector` e implementar estos métodos:

```python
from detectors.base_detector import BaseDetector, DetectorResult, DetectorStatus
from typing import List


class MiNuevoDetector(BaseDetector):
    
    @property
    def name(self) -> str:
        return "MiNuevoDetector"          # Nombre único, sin espacios

    @property
    def description(self) -> str:
        return "Detecta X en el código"   # Una línea descriptiva

    @property
    def severity(self) -> str:
        return "medium"                   # "critical" | "high" | "medium" | "low"

    def analyze(self, file_path: str, content: str) -> List[DetectorResult]:
        results = []
        
        # Tu lógica de análisis aquí
        if "algo_sospechoso" in content:
            results.append(DetectorResult(
                status=DetectorStatus.ERROR,     # OK | WARNING | ERROR
                detector_name=self.name,
                message="Se encontró algo sospechoso",
                details=["Detalle 1", "Sugerencia de corrección"],
                file_path=file_path,
                line_number=1,  # Opcional
            ))
        
        return results
```

---

## 3. Los tres estados posibles

| Estado | Cuándo usarlo | Efecto en el PR |
|--------|---------------|-----------------|
| `DetectorStatus.OK` | Todo correcto | Contribuye al merge automático |
| `DetectorStatus.WARNING` | Posible problema no crítico | Merge con comentario de advertencia |
| `DetectorStatus.ERROR` | Problema crítico confirmado | PR rechazado y cerrado |

---

## 4. Reglas de seguridad para detectores

⚠️ **Tu detector será validado automáticamente** por `DetectorFormatValidator`.

### ✅ Permitido:
```python
import re          # ✅ Regex
import os.path     # ✅ Operaciones de path
from typing import List  # ✅ Type hints
import ast         # ✅ Parsing de código
import hashlib     # ✅ Hashing
```

### ❌ Prohibido (el PR será rechazado):
```python
import subprocess  # ❌ Ejecución de comandos
import socket      # ❌ Conexiones de red
import requests    # ❌ HTTP requests
eval(anything)     # ❌ Evaluación de código
exec(anything)     # ❌ Ejecución de código
```

---

## 5. Omitir archivos innecesarios

Usa `should_skip()` para evitar analizar archivos no relevantes:

```python
def should_skip(self, file_path: str) -> bool:
    # Llamar al padre primero (omite binarios por defecto)
    if super().should_skip(file_path):
        return True
    
    # Tu lógica adicional
    return not file_path.endswith(".py")  # Ej: solo analizar Python
```

---

## 6. Escribir tests

Cada detector debe tener tests en `/tests/`:

```python
# tests/test_mi_nuevo_detector.py
import unittest
from detectors.mi_nuevo_detector import MiNuevoDetector
from detectors.base_detector import DetectorStatus

class TestMiNuevoDetector(unittest.TestCase):
    
    def setUp(self):
        self.detector = MiNuevoDetector()
    
    def test_detects_problem(self):
        content = "código con algo_sospechoso aquí"
        results = self.detector.analyze("archivo.py", content)
        self.assertTrue(any(r.status == DetectorStatus.ERROR for r in results))
    
    def test_clean_code_passes(self):
        content = "código limpio sin problemas"
        results = self.detector.analyze("archivo.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertEqual(len(errors), 0)
    
    def test_false_positive_ignored(self):
        content = "# esto es un comentario con algo_sospechoso"
        results = self.detector.analyze("archivo.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertEqual(len(errors), 0)

if __name__ == "__main__":
    unittest.main()
```

---

## 7. ¿Qué pasa después?

1. Abres un PR con tu nuevo archivo en `/detectors/` y su test en `/tests/`
2. AutoPR Lab analiza automáticamente tu PR
3. `DetectorFormatValidator` valida la estructura de tu detector
4. Si pasa → **merge automático** ✅
5. Si falla → comentario con los problemas específicos ❌

---

## 8. Ejemplos de detectores existentes

| Detector | Detecta | Complejidad |
|----------|---------|-------------|
| `api_keys_detector.py` | API keys y tokens | Media |
| `passwords_detector.py` | Contraseñas hardcodeadas | Media |
| `sensitive_files_detector.py` | Archivos sensibles | Media |
| `detector_validator.py` | Formato de detectores | Alta |

---

## 9. Ideas para nuevos detectores

- `sql_injection_detector.py` — Queries SQL con f-strings/concatenación
- `debug_code_detector.py` — `print()`, `console.log()`, `debugger` en producción
- `todo_comments_detector.py` — TODO/FIXME/HACK en código crítico
- `license_header_detector.py` — Archivos sin header de licencia
- `dependency_version_detector.py` — Dependencias sin versión pinneada

---

¿Tienes dudas? [Abre un issue](../../issues/new) en el repositorio.
