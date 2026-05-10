# Adaptador driven: renderiza Mermaid em PNG/SVG via mermaid.ink (US GD-03).
#
# mermaid.ink e um servico publico gratuito que serve imagens a partir de Mermaid.
# Recebe o codigo Mermaid em base64 url-safe na URL: /img/<base64> (PNG) ou /svg/<base64>.
# Para producao com volume alto, considerar self-hosting do mermaid-cli.

import base64
from typing import Optional

import httpx

from app.application.ports.driven.renderizador_imagem import RenderizadorImagem
from app.domain.excecoes import RenderizadorMermaidError


class RenderizadorMermaidInk(RenderizadorImagem):

    def __init__(
        self,
        base_url: str = "https://mermaid.ink",
        timeout_segundos: float = 20.0,
    ):
        self._base = base_url.rstrip("/")
        self._timeout = timeout_segundos

    def renderizar_mermaid(self, codigo_mermaid: str, formato: str) -> bytes:
        formato_n = (formato or "").lower()
        if formato_n not in ("png", "svg"):
            raise RenderizadorMermaidError(f"formato '{formato}' nao suportado.")

        encoded = base64.urlsafe_b64encode(codigo_mermaid.encode("utf-8")).decode("ascii").rstrip("=")
        prefixo = "img" if formato_n == "png" else "svg"
        url = f"{self._base}/{prefixo}/{encoded}"

        try:
            with httpx.Client(timeout=self._timeout) as cliente:
                resposta = cliente.get(url)
        except httpx.HTTPError as e:
            raise RenderizadorMermaidError(f"erro de rede em mermaid.ink: {e}") from e

        if resposta.status_code != 200:
            raise RenderizadorMermaidError(
                f"mermaid.ink retornou {resposta.status_code}: {resposta.text[:200]}"
            )
        return resposta.content


# Marcadores PNG/SVG falsos so para sinalizar que o adapter nao faz IO real nos testes.
_PNG_FAKE = b"\x89PNG\r\n\x1a\nFAKE_MERMAID"
_SVG_FAKE = b'<svg xmlns="http://www.w3.org/2000/svg"><text>FAKE_MERMAID</text></svg>'


class RenderizadorMermaidFake(RenderizadorImagem):
    """Fake para testes — devolve bytes simbolicos (mantem magic bytes corretos)."""

    def __init__(self):
        self._falha: Optional[Exception] = None
        self.chamadas: list = []

    def fazer_falhar_com(self, exc: Exception) -> None:
        self._falha = exc

    def renderizar_mermaid(self, codigo_mermaid: str, formato: str) -> bytes:
        self.chamadas.append((codigo_mermaid, formato))
        if self._falha is not None:
            raise self._falha
        f = (formato or "").lower()
        if f == "png":
            return _PNG_FAKE
        if f == "svg":
            return _SVG_FAKE
        raise RenderizadorMermaidError(f"formato '{formato}' desconhecido no fake.")
