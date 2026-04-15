#!/usr/bin/env python3
"""
AutoPR Lab - Detectors Validator Script
========================================
Valida todos los detectores del proyecto usando el DetectorFormatValidator.
"""

import os
import sys
from typing import Any, cast

# Agregar el directorio raíz y src al path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "src"))

from detectors import discover_detectors  # noqa: E402
from detectors.detector_validator import DetectorFormatValidator  # noqa: E402


def validate_all() -> None:
    print("Validando estructura de detectores registrados...")

    validator = DetectorFormatValidator()
    detector_classes = discover_detectors()

    detectors_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "detectors"
    )

    any_error = False
    results = []

    for cls in detector_classes:
        # Obtener el path del archivo de la clase
        module = sys.modules.get(cls.__module__)
        if not module or not hasattr(module, "__file__") or not module.__file__:
            continue

        file_path = module.__file__
        rel_path = os.path.relpath(file_path, os.path.dirname(detectors_dir))

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        findings = validator.analyze(rel_path, content)

        # Filtrar solo errores
        errors = [f for f in findings if f.status == "ERROR"]
        is_valid = len(errors) == 0

        if not is_valid:
            any_error = True

        results.append(
            {
                "name": cls.__name__,
                "path": rel_path,
                "is_valid": is_valid,
                "errors": [f.message for f in errors],
            }
        )

    print(f"Validacion completada: {len(results)} detectores verificados")
    for r in results:
        data = cast(dict[str, Any], r)
        status = "OK" if data["is_valid"] else "FAIL"
        print(f"  [{status}] {data['name']} ({data['path']})")
        for err in cast(list[str], data["errors"]):
            print(f"     └─ ERROR: {err}")

    if any_error:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    validate_all()
