# Adaptador driven: HTTP client para IA-Analise-Codigo (US GD-03).

from typing import Any, Dict, Optional

import httpx

from app.application.ports.driven.cliente_ia_analise import ClienteIAAnalise
from app.domain.excecoes import IAAnaliseIndisponivelError


class ClienteIAAnaliseHTTP(ClienteIAAnalise):

    def __init__(self, base_url: str, timeout_segundos: float = 30.0):
        self._base = base_url.rstrip("/")
        self._timeout = timeout_segundos

    def gerar_diagrama_de_codigo(self, codigo: str, tipo: str = "classe") -> Dict[str, Any]:
        url = f"{self._base}/estrutura/diagrama"
        try:
            with httpx.Client(timeout=self._timeout) as cliente:
                resposta = cliente.post(url, json={"codigo": codigo, "tipo": tipo})
        except httpx.HTTPError as e:
            raise IAAnaliseIndisponivelError(
                f"erro de rede ao chamar IA-Analise: {e}"
            ) from e

        if resposta.status_code == 400:
            raise IAAnaliseIndisponivelError(
                f"IA-Analise rejeitou o codigo: {resposta.text[:200]}"
            )
        if resposta.status_code != 200:
            raise IAAnaliseIndisponivelError(
                f"IA-Analise retornou {resposta.status_code}: {resposta.text[:200]}"
            )
        try:
            return resposta.json()
        except ValueError as e:
            raise IAAnaliseIndisponivelError(f"resposta da IA-Analise nao e JSON: {e}") from e


class ClienteIAAnaliseFake(ClienteIAAnalise):
    """Fake para testes — devolve dicionario configurado ou levanta excecao."""

    def __init__(self):
        self._proxima_resposta: Optional[Dict[str, Any]] = None
        self._falha: Optional[Exception] = None
        self.chamadas: list = []

    def configurar_resposta(self, resposta: Dict[str, Any]) -> None:
        self._proxima_resposta = resposta
        self._falha = None

    def fazer_falhar_com(self, exc: Exception) -> None:
        self._falha = exc
        self._proxima_resposta = None

    def gerar_diagrama_de_codigo(self, codigo: str, tipo: str = "classe") -> Dict[str, Any]:
        self.chamadas.append({"codigo": codigo, "tipo": tipo})
        if self._falha is not None:
            raise self._falha
        return dict(self._proxima_resposta or {
            "componentes": [], "relacoes": [], "mermaid": "classDiagram\n",
            "warnings": [], "linguagem": "python",
        })
