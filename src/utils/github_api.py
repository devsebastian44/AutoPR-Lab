"""
AutoPR Lab - GitHub API Client
================================
Wrapper para operaciones de la GitHub API:
aprobar, rechazar, mergear y comentar en PRs.
"""

import json
import urllib.error
import urllib.request
from typing import Any, cast

from utils.logger import get_logger

logger = get_logger("github_api")


class GitHubAPIError(Exception):
    """Error de la API de GitHub."""

    def __init__(self, message: str, status_code: int = 0, response: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class GitHubAPI:
    """
    Cliente para la GitHub REST API v3.
    Usa solo módulos de la biblioteca estándar (sin requests).
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str, repo: str, pr_number: int):
        """
        Args:
            token: GitHub token (GITHUB_TOKEN del workflow)
            repo: Repositorio en formato "owner/repo"
            pr_number: Número del Pull Request
        """
        self.token = token
        self.repo = repo
        self.pr_number = pr_number

    def _request(
        self,
        method: str,
        endpoint: str,
        body: dict[str, Any] | None = None,
        accept: str = "application/vnd.github+json",
    ) -> Any:
        """Realiza una petición a la GitHub API."""
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "AutoPR-Lab/1.0",
        }

        data = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req) as response:  # nosec B310
                response_body = response.read().decode("utf-8")
                return json.loads(response_body) if response_body.strip() else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise GitHubAPIError(
                f"GitHub API {method} {url} → {e.code}: {error_body}",
                status_code=e.code,
                response=error_body,
            ) from e

    # ── Información del PR ──────────────────────────────────────────────

    def get_pr_info(self) -> dict[str, Any]:
        """Obtiene información del PR."""
        return cast(
            dict[str, Any],
            self._request("GET", f"repos/{self.repo}/pulls/{self.pr_number}"),
        )

    def get_changed_files(self) -> list[dict[str, Any]]:
        """Obtiene lista de archivos modificados en el PR."""
        files = []
        page = 1
        while True:
            result = self._request(
                "GET",
                f"repos/{self.repo}/pulls/{self.pr_number}/files?per_page=100&page={page}",
            )
            if not result:
                break
            files.extend(result)
            if len(result) < 100:
                break
            page += 1
        return files

    def get_file_content(self, raw_url: str) -> str:
        """Descarga el contenido de un archivo del PR usando su raw_url."""
        if not raw_url.startswith("https://"):
            logger.warning(
                f"URL rechazada por seguridad (solo https permitido): {raw_url}"
            )
            return ""

        req = urllib.request.Request(
            raw_url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "AutoPR-Lab/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req) as response:  # nosec B310
                return cast(str, response.read().decode("utf-8", errors="replace"))
        except Exception as e:
            logger.warning(f"No se pudo descargar {raw_url}: {e}")
            return ""

    def get_file_content_by_path(self, path: str, ref: str) -> str:
        """
        Descarga el contenido de un archivo usando la API de contenidos.
        Útil si no se dispone de raw_url o para una revisión específica.
        """
        import base64

        try:
            result = self._request(
                "GET", f"repos/{self.repo}/contents/{path}?ref={ref}"
            )
            content_b64 = result.get("content", "")
            if content_b64:
                return base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"No se pudo descargar {path} en {ref}: {e}")
        return ""

    # ── Acciones sobre el PR ────────────────────────────────────────────

    def add_comment(self, body: str) -> dict[str, Any]:
        """Agrega un comentario al PR."""
        logger.info(f"💬 Agregando comentario al PR #{self.pr_number}")
        return cast(
            dict[str, Any],
            self._request(
                "POST",
                f"repos/{self.repo}/issues/{self.pr_number}/comments",
                body={"body": body},
            ),
        )

    def approve_pr(
        self, message: str = "AutoPR Lab: ✅ Aprobado automáticamente"
    ) -> dict[str, Any]:
        """Aprueba el PR con un review."""
        logger.info(f"✅ Aprobando PR #{self.pr_number}")
        return cast(
            dict[str, Any],
            self._request(
                "POST",
                f"repos/{self.repo}/pulls/{self.pr_number}/reviews",
                body={"body": message, "event": "APPROVE"},
            ),
        )

    def request_changes(self, message: str) -> dict[str, Any]:
        """Solicita cambios en el PR (REQUEST_CHANGES review)."""
        logger.info(f"❌ Solicitando cambios en PR #{self.pr_number}")
        return cast(
            dict[str, Any],
            self._request(
                "POST",
                f"repos/{self.repo}/pulls/{self.pr_number}/reviews",
                body={"body": message, "event": "REQUEST_CHANGES"},
            ),
        )

    def merge_pr(
        self,
        commit_title: str | None = None,
        commit_message: str | None = None,
        merge_method: str = "squash",
    ) -> dict[str, Any]:
        """
        Hace merge del PR.

        Args:
            merge_method: "merge" | "squash" | "rebase"
        """
        logger.info(f"🔀 Mergeando PR #{self.pr_number} con método '{merge_method}'")

        pr_info = self.get_pr_info()
        sha = pr_info.get("head", {}).get("sha", "")

        body = {
            "merge_method": merge_method,
            "sha": sha,
        }
        if commit_title:
            body["commit_title"] = commit_title
        if commit_message:
            body["commit_message"] = commit_message

        try:
            return cast(
                dict[str, Any],
                self._request(
                    "PUT",
                    f"repos/{self.repo}/pulls/{self.pr_number}/merge",
                    body=body,
                ),
            )
        except GitHubAPIError as e:
            if e.status_code == 405:
                raise GitHubAPIError(
                    "El PR no puede ser mergeado (puede estar desactualizado o tener conflictos)",
                    status_code=e.status_code,
                ) from e
            raise

    def close_pr(self) -> dict[str, Any]:
        """Cierra el PR sin hacer merge."""
        logger.info(f"🚫 Cerrando PR #{self.pr_number}")
        return cast(
            dict[str, Any],
            self._request(
                "PATCH",
                f"repos/{self.repo}/pulls/{self.pr_number}",
                body={"state": "closed"},
            ),
        )

    def add_label(self, label: str) -> dict[str, Any]:
        """Agrega un label al PR."""
        return cast(
            dict[str, Any],
            self._request(
                "POST",
                f"repos/{self.repo}/issues/{self.pr_number}/labels",
                body={"labels": [label]},
            ),
        )
