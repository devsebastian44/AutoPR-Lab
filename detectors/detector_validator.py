"""
AutoPR Lab - Detector Format Validator
========================================
Valida que los detectores nuevos cumplan con la estructura requerida.
Protección contra contribuciones maliciosas o mal formadas.
"""

import ast
import os

from detectors.base_detector import BaseDetector, DetectorResult, DetectorStatus


class DetectorFormatValidator(BaseDetector):
    """
    Valida la estructura y seguridad de los detectores nuevos en el PR.
    Este detector es especial: analiza código Python de otros detectores.
    """

    # Imports prohibidos en detectores (podrían ejecutar código arbitrario o red)
    FORBIDDEN_IMPORTS = {
        "subprocess",
        "os.system",
        "eval",
        "exec",
        "importlib",
        "pty",
        "pexpect",
        "socket",
        "requests",
        "urllib",
        "http.client",
        "ftplib",
        "smtplib",
        "poplib",
        "ctypes",
        "cffi",
        "sys",
        "shutil",
        "posix",
        "__import__",
        "pickle",
        "marshal",
        "shelve",
    }

    # Funciones peligrosas (built-ins y de módulos comunes)
    FORBIDDEN_FUNCTIONS = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "open",
        "system",
        "popen",
        "spawnl",
        "spawnv",
        "spawnlp",
        "spawnvp",
        "execl",
        "execv",
        "execle",
        "execve",
        "execlp",
        "execvp",
        "run",
        "call",
        "check_call",
        "check_output",
        "getstatusoutput",
        "getoutput",
    }

    # Atributos requeridos en todo detector
    REQUIRED_PROPERTIES = {"name", "description", "severity", "analyze"}

    @property
    def name(self) -> str:
        return "DetectorFormatValidator"

    @property
    def description(self) -> str:
        return "Valida que los detectores nuevos siguen la estructura requerida y no contienen código peligroso"

    @property
    def severity(self) -> str:
        return "critical"

    def should_skip(self, file_path: str) -> bool:
        # Solo analizar archivos Python en /detectors/
        if not file_path.endswith(".py"):
            return True
        if "detectors/" not in file_path and "detectors\\" not in file_path:
            return True
        # No analizarse a sí mismo ni al base
        filename = os.path.basename(file_path)
        if filename in ("base_detector.py", "detector_validator.py", "__init__.py"):
            return True
        return False

    def _check_forbidden_imports(
        self, tree: ast.AST, file_path: str
    ) -> list[DetectorResult]:
        results = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                else:
                    modules = [node.module] if node.module else []

                for module in modules:
                    if module and any(
                        module.startswith(forbidden)
                        for forbidden in self.FORBIDDEN_IMPORTS
                    ):
                        results.append(
                            DetectorResult(
                                status=DetectorStatus.ERROR,
                                detector_name=self.name,
                                message=f"Import prohibido en detector: `{module}`",
                                details=[
                                    "Los detectores no pueden importar módulos de red o ejecución de código.",
                                    f"Módulo bloqueado: `{module}`",
                                    "Los detectores solo pueden usar: re, os.path, typing, y módulos estándar seguros.",
                                ],
                                file_path=file_path,
                                line_number=node.lineno,
                            )
                        )
        return results

    def _check_forbidden_calls(
        self, tree: ast.AST, file_path: str
    ) -> list[DetectorResult]:
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name and func_name in self.FORBIDDEN_FUNCTIONS:
                    results.append(
                        DetectorResult(
                            status=DetectorStatus.ERROR,
                            detector_name=self.name,
                            message=f"Función peligrosa en detector: `{func_name}()`",
                            details=[
                                f"`{func_name}()` puede ejecutar código arbitrario o acceder al sistema y está prohibida.",
                                "Los detectores solo deben analizar texto, no ejecutar código ni realizar operaciones de sistema.",
                            ],
                            file_path=file_path,
                            line_number=getattr(node, "lineno", None),
                        )
                    )
        return results

    def _check_inherits_base(
        self, tree: ast.AST, file_path: str
    ) -> list[DetectorResult]:
        results = []
        found_detector_class = False

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_names = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_names.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_names.append(base.attr)

                if "BaseDetector" in base_names:
                    found_detector_class = True

                    # Verificar que implementa los métodos requeridos
                    implemented = set()
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            implemented.add(item.name)

                    missing = self.REQUIRED_PROPERTIES - implemented
                    if missing:
                        results.append(
                            DetectorResult(
                                status=DetectorStatus.ERROR,
                                detector_name=self.name,
                                message=f"Detector `{node.name}` no implementa métodos requeridos",
                                details=[
                                    f"Métodos/propiedades faltantes: {', '.join(f'`{m}`' for m in missing)}",
                                    "Todo detector debe implementar: `name`, `description`, `severity`, `analyze`",
                                ],
                                file_path=file_path,
                                line_number=node.lineno,
                            )
                        )

        if not found_detector_class:
            results.append(
                DetectorResult(
                    status=DetectorStatus.ERROR,
                    detector_name=self.name,
                    message="El archivo no contiene ninguna clase que herede de `BaseDetector`",
                    details=[
                        "Los detectores deben heredar de `BaseDetector`.",
                        "Ejemplo: `class MyDetector(BaseDetector):`",
                        "Ver: docs/how-to-add-detector.md",
                    ],
                    file_path=file_path,
                )
            )

        return results

    def analyze(self, file_path: str, content: str) -> list[DetectorResult]:
        if self.should_skip(file_path):
            return []

        results = []

        # Intentar parsear el AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return [
                DetectorResult(
                    status=DetectorStatus.ERROR,
                    detector_name=self.name,
                    message=f"Error de sintaxis en el detector: {e.msg}",
                    details=[f"Línea {e.lineno}: {e.text}"],
                    file_path=file_path,
                    line_number=e.lineno,
                )
            ]

        results.extend(self._check_forbidden_imports(tree, file_path))
        results.extend(self._check_forbidden_calls(tree, file_path))
        results.extend(self._check_inherits_base(tree, file_path))

        if not results:
            results.append(
                DetectorResult(
                    status=DetectorStatus.OK,
                    detector_name=self.name,
                    message="Estructura del detector válida",
                    details=[
                        "El detector cumple con todos los requisitos de formato y seguridad."
                    ],
                    file_path=file_path,
                )
            )

        return results
