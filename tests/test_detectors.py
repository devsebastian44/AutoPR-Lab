"""
AutoPR Lab - Tests para Detectores
=====================================
Tests unitarios para validar que los detectores funcionan correctamente.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from detectors.api_keys_detector import APIKeysDetector
from detectors.base_detector import DetectorStatus
from detectors.passwords_detector import PasswordsDetector
from detectors.sensitive_files_detector import SensitiveFilesDetector


class TestAPIKeysDetector(unittest.TestCase):
    def setUp(self):
        self.detector = APIKeysDetector()

    def test_detects_github_token(self):
        content = 'TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxyz12"'
        results = self.detector.analyze("config.py", content)
        self.assertTrue(any(r.status == DetectorStatus.ERROR for r in results))

    def test_detects_openai_key(self):
        content = 'OPENAI_KEY = "sk-abcdefghijklmnopqrstuvwxyz1234567890abcdefghijk"'
        results = self.detector.analyze("app.py", content)
        self.assertTrue(any(r.status == DetectorStatus.ERROR for r in results))

    def test_detects_rsa_private_key(self):
        content = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA..."
        results = self.detector.analyze("key.txt", content)
        self.assertTrue(any(r.status == DetectorStatus.ERROR for r in results))

    def test_detects_database_url_with_credentials(self):
        content = 'DATABASE_URL = "postgresql://user:mypassword123@localhost/mydb"'
        results = self.detector.analyze("settings.py", content)
        self.assertTrue(any(r.status == DetectorStatus.ERROR for r in results))

    def test_ignores_env_var_reading(self):
        """El código que LEE variables de entorno es seguro."""
        content = 'api_key = os.getenv("MY_API_KEY")'
        results = self.detector.analyze("app.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertEqual(len(errors), 0)

    def test_ignores_placeholder(self):
        """Los placeholders en templates no son errores."""
        content = "API_KEY=your_api_key_here"
        results = self.detector.analyze("README.md", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertEqual(len(errors), 0)

    def test_skips_binary_files(self):
        content = "binary content"
        results = self.detector.analyze("image.png", content)
        self.assertEqual(len(results), 0)


class TestPasswordsDetector(unittest.TestCase):
    def setUp(self):
        self.detector = PasswordsDetector()

    def test_detects_hardcoded_password(self):
        content = 'password = "mysecretpassword123"'
        results = self.detector.analyze("config.py", content)
        self.assertTrue(any(r.status == DetectorStatus.ERROR for r in results))

    def test_detects_trivial_password(self):
        content = 'PASSWORD = "admin"'
        results = self.detector.analyze("settings.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertTrue(len(errors) > 0)
        # Verificar que menciona que es trivial
        has_trivial_warning = any(
            "trivial" in str(r.details).lower() or "crítico" in str(r.details).lower()
            for r in errors
        )
        self.assertTrue(has_trivial_warning)

    def test_detects_json_credential(self):
        content = '{"password": "secretvalue123"}'
        results = self.detector.analyze("config.json", content)
        self.assertTrue(any(r.status == DetectorStatus.ERROR for r in results))

    def test_ignores_env_var_access(self):
        content = 'db_pass = os.getenv("DB_PASSWORD")'
        results = self.detector.analyze("db.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertEqual(len(errors), 0)

    def test_ignores_commented_line(self):
        content = '# password = "example_do_not_use"'
        results = self.detector.analyze("example.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertEqual(len(errors), 0)


class TestSensitiveFilesDetector(unittest.TestCase):
    def setUp(self):
        self.detector = SensitiveFilesDetector()

    def test_detects_env_file(self):
        content = "API_KEY=real_value_123\nDB_PASS=secret"
        results = self.detector.analyze(".env", content)
        self.assertTrue(any(r.status == DetectorStatus.ERROR for r in results))

    def test_detects_env_production(self):
        content = "PROD_SECRET=actualvalue123"
        results = self.detector.analyze(".env.production", content)
        self.assertTrue(any(r.status == DetectorStatus.ERROR for r in results))

    def test_detects_private_key_content(self):
        content = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkq...\n-----END PRIVATE KEY-----"
        results = self.detector.analyze("any_file.txt", content)
        self.assertTrue(any(r.status == DetectorStatus.ERROR for r in results))

    def test_detects_aws_credentials_file(self):
        content = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        results = self.detector.analyze(".aws/credentials", content)
        self.assertTrue(any(r.status == DetectorStatus.ERROR for r in results))

    def test_warns_on_template_file(self):
        content = "API_KEY=YOUR_API_KEY_HERE\nDB_PASS=your_password_here"
        results = self.detector.analyze(".env.example", content)
        # Template sin valores reales = WARNING, no ERROR
        statuses = [r.status for r in results]
        self.assertIn(DetectorStatus.WARNING, statuses)
        self.assertNotIn(DetectorStatus.ERROR, statuses)

    def test_error_on_template_with_real_values(self):
        content = "-----BEGIN RSA PRIVATE KEY-----\nrealkey..."
        results = self.detector.analyze(".env.example", content)
        self.assertTrue(any(r.status == DetectorStatus.ERROR for r in results))

    def test_normal_python_file_is_ok(self):
        content = "def hello():\n    return 'Hello, World!'"
        results = self.detector.analyze("hello.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertEqual(len(errors), 0)


class TestDetectorFormatValidator(unittest.TestCase):
    def setUp(self):
        from detectors.detector_validator import DetectorFormatValidator

        self.validator = DetectorFormatValidator()

    def test_valid_detector_structure(self):
        content = """
from detectors.base_detector import BaseDetector, DetectorResult, DetectorStatus
from typing import List

class MyDetector(BaseDetector):
    @property
    def name(self): return "MyDetector"

    @property
    def description(self): return "Test detector"

    @property
    def severity(self): return "medium"

    def analyze(self, file_path: str, content: str) -> List[DetectorResult]:
        return []
"""
        results = self.validator.analyze("detectors/my_detector.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertEqual(len(errors), 0)

    def test_rejects_subprocess_import(self):
        content = """
import subprocess
from detectors.base_detector import BaseDetector, DetectorResult, DetectorStatus
from typing import List

class MaliciousDetector(BaseDetector):
    @property
    def name(self): return "MaliciousDetector"
    @property
    def description(self): return "Bad detector"
    @property
    def severity(self): return "low"
    def analyze(self, fp, content): return []
"""
        results = self.validator.analyze("detectors/malicious.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertTrue(len(errors) > 0)

    def test_rejects_eval_usage(self):
        content = """
from detectors.base_detector import BaseDetector, DetectorResult, DetectorStatus
from typing import List

class EvalDetector(BaseDetector):
    @property
    def name(self): return "EvalDetector"
    @property
    def description(self): return "Uses eval"
    @property
    def severity(self): return "low"
    def analyze(self, fp, content):
        eval(content)  # PELIGROSO
        return []
"""
        results = self.validator.analyze("detectors/eval_detector.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertTrue(len(errors) > 0)

    def test_rejects_missing_base_class(self):
        content = """
class NotADetector:
    def analyze(self, fp, content):
        return []
"""
        results = self.validator.analyze("detectors/not_a_detector.py", content)
        errors = [r for r in results if r.status == DetectorStatus.ERROR]
        self.assertTrue(len(errors) > 0)


if __name__ == "__main__":
    # Colorear output de tests
    import unittest

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_class in [
        TestAPIKeysDetector,
        TestPasswordsDetector,
        TestSensitiveFilesDetector,
        TestDetectorFormatValidator,
    ]:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
