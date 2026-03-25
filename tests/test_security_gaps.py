"""
AutoPR Lab - Security Regression Tests
========================================
Valida que el DetectorFormatValidator bloquee correctamente nuevos vectores de ataque.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from detectors.base_detector import DetectorStatus
from detectors.detector_validator import DetectorFormatValidator


class TestSecurityRegression(unittest.TestCase):
    def setUp(self):
        self.validator = DetectorFormatValidator()

    def test_rejects_os_system_call(self):
        content = """
import os
from detectors.base_detector import BaseDetector

class AttackDetector(BaseDetector):
    @property
    def name(self): return "Attack"
    @property
    def description(self): return "x"
    @property
    def severity(self): return "low"
    def analyze(self, fp, content):
        os.system("rm -rf /")  # DEBE SER RECHAZADO
        return []
"""
        results = self.validator.analyze("detectors/attack.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertTrue(
            any("system()" in r.message for r in errors),
            "Debería haber bloqueado os.system()",
        )

    def test_rejects_subprocess_run(self):
        content = """
import subprocess
from detectors.base_detector import BaseDetector

class AttackDetector(BaseDetector):
    @property
    def name(self): return "Attack"
    @property
    def description(self): return "x"
    @property
    def severity(self): return "low"
    def analyze(self, fp, content):
        subprocess.run(["ls"])  # DEBE SER RECHAZADO
        return []
"""
        results = self.validator.analyze("detectors/attack2.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertTrue(
            any("run()" in r.message for r in errors),
            "Debería haber bloqueado subprocess.run()",
        )

    def test_rejects_shutil_import(self):
        content = """
import shutil
from detectors.base_detector import BaseDetector

class AttackDetector(BaseDetector):
    @property
    def name(self): return "Attack"
    @property
    def description(self): return "x"
    @property
    def severity(self): return "low"
    def analyze(self, fp, content):
        return []
"""
        results = self.validator.analyze("detectors/attack3.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertTrue(
            any("shutil" in r.message for r in errors),
            "Debería haber bloqueado import shutil",
        )

    def test_rejects_pickle_import(self):
        content = """
import pickle
from detectors.base_detector import BaseDetector

class AttackDetector(BaseDetector):
    @property
    def name(self): return "Attack"
    @property
    def description(self): return "x"
    @property
    def severity(self): return "low"
    def analyze(self, fp, content):
        return []
"""
        results = self.validator.analyze("detectors/attack4.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertTrue(
            any("pickle" in r.message for r in errors),
            "Debería haber bloqueado import pickle",
        )

    def test_rejects_builtin_open(self):
        content = """
from detectors.base_detector import BaseDetector

class AttackDetector(BaseDetector):
    @property
    def name(self): return "Attack"
    @property
    def description(self): return "x"
    @property
    def severity(self): return "low"
    def analyze(self, fp, content):
        with open("/etc/passwd") as f: # DEBE SER RECHAZADO
            pass
        return []
"""
        results = self.validator.analyze("detectors/attack5.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertTrue(
            any("open()" in r.message for r in errors), "Debería haber bloqueado open()"
        )


if __name__ == "__main__":
    unittest.main()
