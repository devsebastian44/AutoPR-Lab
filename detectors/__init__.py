"""
AutoPR Lab - Detectors Package
================================
Auto-descubrimiento de detectores.
Cualquier clase que herede de BaseDetector es registrada automáticamente.
"""

import importlib
import inspect
import os

from detectors.base_detector import BaseDetector


def discover_detectors() -> list[type[BaseDetector]]:
    """
    Descubre automáticamente todos los detectores en este paquete.
    No necesitas registrarlos manualmente.
    """
    detectors = []
    detectors_dir = os.path.dirname(__file__)

    for filename in sorted(os.listdir(detectors_dir)):
        if filename.endswith(".py") and filename not in (
            "__init__.py",
            "base_detector.py",
        ):
            module_name = filename[:-3]  # quitar .py
            try:
                module = importlib.import_module(f"detectors.{module_name}")
                for _name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, BaseDetector)
                        and obj is not BaseDetector
                        and obj.__module__ == module.__name__
                    ):
                        detectors.append(obj)
            except ImportError as e:
                print(f"[WARN] No se pudo cargar detector {module_name}: {e}")

    return detectors


__all__ = ["BaseDetector", "discover_detectors"]
