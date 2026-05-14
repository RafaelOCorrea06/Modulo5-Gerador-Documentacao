# Adaptador driven: busca arquivo na branch via GitHub Contents API (US GD-03).

import base64
from typing import Optional

import httpx

from app.application.ports.driven.fonte_codigo import FonteCodigo
from app.domain.excecoes import FonteCodigoIndisponivelError


class FonteCodigoGitHubHTTP(FonteCodigo):

    def __init__(
        self,
        base_url: str = "https://api.github.com",
        token: Optional[str] = None,
        timeout_segundos: float = 10.0,
    ):
        self._base = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout_segundos

    def obter_arquivo_em_branch(
        self, repositorio: str, branch: str, arquivo: str,
    ) -> str:
        url = f"{self._base}/repos/{repositorio}/contents/{arquivo}"
        cabecalhos = {"Accept": "application/vnd.github+json"}
        if self._token:
            cabecalhos["Authorization"] = f"Bearer {self._token}"

        try:
            with httpx.Client(timeout=self._timeout) as cliente:
                resposta = cliente.get(url, headers=cabecalhos, params={"ref": branch})
        except httpx.HTTPError as e:
            raise FonteCodigoIndisponivelError(
                f"erro de rede ao buscar {arquivo}@{branch}: {e}"
            ) from e

        if resposta.status_code == 404:
            raise FonteCodigoIndisponivelError(
                f"Arquivo '{arquivo}' nao encontrado em '{repositorio}' na branch '{branch}'."
            )
        if resposta.status_code in (403, 429):
            raise FonteCodigoIndisponivelError(
                f"GitHub bloqueou ({resposta.status_code}) — possivel rate limit. "
                f"Configure GITHUB_TOKEN para aumentar a cota."
            )
        if resposta.status_code != 200:
            raise FonteCodigoIndisponivelError(
                f"GitHub retornou {resposta.status_code}: {resposta.text[:200]}"
            )

        payload = resposta.json()
        if payload.get("encoding") != "base64":
            raise FonteCodigoIndisponivelError(
                f"Encoding inesperado do GitHub: {payload.get('encoding')}"
            )
        return base64.b64decode(payload.get("content", "")).decode("utf-8", errors="replace")


class FonteCodigoFake(FonteCodigo):
    """Fake para testes — pre-configura conteudo por (repo, branch, arquivo)."""

    def __init__(self):
        self._conteudo = {}
        self._falha: Optional[Exception] = None

    def configurar(self, repo: str, branch: str, arquivo: str, conteudo: str) -> None:
        self._conteudo[(repo, branch, arquivo)] = conteudo
        self._falha = None

    def fazer_falhar_com(self, exc: Exception) -> None:
        self._falha = exc

    def obter_arquivo_em_branch(self, repositorio: str, branch: str, arquivo: str) -> str:
        if self._falha is not None:
            raise self._falha
        chave = (repositorio, branch, arquivo)
        if chave not in self._conteudo:
            raise FonteCodigoIndisponivelError(
                f"Fake nao tem '{arquivo}' em '{repositorio}@{branch}' configurado."
            )
        return self._conteudo[chave]
