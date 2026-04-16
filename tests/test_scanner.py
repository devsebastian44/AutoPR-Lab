"""
AutoPR Lab - Tests para el Scanner
=====================================
Tests de integración para el motor principal de análisis.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from core.scanner import Scanner, SecurityRules


class TestSecurityRules(unittest.TestCase):
    """Tests para las reglas de seguridad de paths."""

    def test_allowed_paths_accepted(self):
        files = [
            "src/detectors/my_new_detector.py",
            "tests/test_my_detector.py",
            "docs/guide.md",
        ]
        is_valid, violations = SecurityRules.validate_paths(files)
        self.assertTrue(is_valid, f"Debería ser válido. Violations: {violations}")
        self.assertEqual(len(violations), 0)

    def test_forbidden_core_path_blocked(self):
        files = ["src/core/scanner.py"]
        is_valid, violations = SecurityRules.validate_paths(files)
        self.assertFalse(is_valid)
        self.assertTrue(len(violations) > 0)

    def test_forbidden_workflow_path_blocked(self):
        files = [".github/workflows/auto-pr.yml"]
        is_valid, violations = SecurityRules.validate_paths(files)
        self.assertFalse(is_valid)
        self.assertTrue(len(violations) > 0)

    def test_forbidden_requirements_blocked(self):
        files = ["requirements.txt"]
        is_valid, violations = SecurityRules.validate_paths(files)
        self.assertFalse(is_valid)

    def test_mixed_allowed_and_forbidden(self):
        files = [
            "src/detectors/new_detector.py",  # OK
            "src/core/scanner.py",  # FORBIDDEN
        ]
        is_valid, violations = SecurityRules.validate_paths(files)
        self.assertFalse(is_valid)
        self.assertEqual(len(violations), 1)

    def test_size_limit_files(self):
        is_valid, violations = SecurityRules.validate_size(
            num_files=SecurityRules.MAX_FILES + 1, lines_changed=10
        )
        self.assertFalse(is_valid)
        self.assertTrue(len(violations) > 0)

    def test_size_limit_lines(self):
        is_valid, violations = SecurityRules.validate_size(
            num_files=1, lines_changed=SecurityRules.MAX_LINES_CHANGED + 1
        )
        self.assertFalse(is_valid)

    def test_size_within_limits(self):
        is_valid, violations = SecurityRules.validate_size(
            num_files=3, lines_changed=100
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)


class TestScannerIntegration(unittest.TestCase):
    """Tests de integración del scanner completo."""

    def setUp(self):
        self.scanner = Scanner()

    def test_clean_detector_gets_merge(self):
        """Un detector limpio y válido debe resultar en MERGE."""
        changed_files = {
            "src/detectors/my_clean_detector.py": """
from detectors.base_detector import BaseDetector, DetectorResult, DetectorStatus
from typing import List

class MyCleanDetector(BaseDetector):
    @property
    def name(self): return "MyCleanDetector"
    @property
    def description(self): return "A clean detector"
    @property
    def severity(self): return "low"
    def analyze(self, file_path: str, content: str) -> List[DetectorResult]:
        return []
""",
            "tests/test_my_clean_detector.py": """
import unittest
class TestMyCleanDetector(unittest.TestCase):
    def test_basic(self):
        self.assertTrue(True)
""",
        }

        result = self.scanner.scan_pr(
            pr_number=1,
            changed_files=changed_files,
            lines_changed=30,
        )

        self.assertEqual(result.global_status, "OK")
        self.assertEqual(result.decision, "MERGE")
        self.assertEqual(result.errors, 0)

    def test_api_key_in_detector_gets_rejected(self):
        """Un detector con API key hardcodeada debe ser rechazado."""
        changed_files = {
            "src/detectors/bad_detector.py": """
from detectors.base_detector import BaseDetector, DetectorResult, DetectorStatus
from typing import List

OPENAI_KEY = "sk-abcdefghijklmnopqrstuvwxyz1234567890abcdefghijk"

class BadDetector(BaseDetector):
    @property
    def name(self): return "BadDetector"
    @property
    def description(self): return "Has a hardcoded key"
    @property
    def severity(self): return "low"
    def analyze(self, fp, content): return []
""",
        }

        result = self.scanner.scan_pr(
            pr_number=2,
            changed_files=changed_files,
            lines_changed=15,
        )

        self.assertEqual(result.global_status, "ERROR")
        self.assertEqual(result.decision, "REJECT")
        self.assertGreater(result.errors, 0)

    def test_core_modification_gets_rejected(self):
        """Modificar /core/ debe ser rechazado independientemente del contenido."""
        changed_files = {
            "src/core/scanner.py": "# Perfectly clean code\nprint('hello')",
        }

        result = self.scanner.scan_pr(
            pr_number=3,
            changed_files=changed_files,
            lines_changed=2,
        )

        self.assertEqual(result.decision, "REJECT")
        self.assertFalse(result.path_validation.get("paths_ok", True))

    def test_workflow_modification_gets_rejected(self):
        """Modificar workflows de GitHub Actions debe ser rechazado."""
        changed_files = {
            ".github/workflows/auto-pr.yml": "name: Malicious workflow",
        }

        result = self.scanner.scan_pr(
            pr_number=4,
            changed_files=changed_files,
            lines_changed=1,
        )

        self.assertEqual(result.decision, "REJECT")

    def test_env_file_gets_rejected(self):
        """Incluir .env en el PR debe resultar en REJECT."""
        changed_files = {
            ".env": "API_KEY=real_secret_value\nDB_PASSWORD=actual_password",
        }

        result = self.scanner.scan_pr(
            pr_number=5,
            changed_files=changed_files,
            lines_changed=2,
        )

        self.assertEqual(result.decision, "REJECT")

    def test_result_has_required_fields(self):
        """El resultado debe tener todos los campos requeridos."""
        result = self.scanner.scan_pr(
            pr_number=99,
            changed_files={"docs/readme.md": "# Documentation"},
            lines_changed=1,
        )

        self.assertIsNotNone(result.global_status)
        self.assertIsNotNone(result.decision)
        self.assertIsNotNone(result.detectors_run)
        self.assertIsInstance(result.detectors_run, list)
        self.assertGreater(len(result.detectors_run), 0)
        self.assertIsNotNone(result.timestamp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
