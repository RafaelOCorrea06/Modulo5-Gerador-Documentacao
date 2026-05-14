# Porta driven: RenderizadorImagem (US GD-03)
# Abstrai a renderizacao de Mermaid em PNG/SVG.

from abc import ABC, abstractmethod


class RenderizadorImagem(ABC):

    @abstractmethod
    def renderizar_mermaid(self, codigo_mermaid: str, formato: str) -> bytes:
        """
        Devolve os bytes da imagem (PNG ou SVG) renderizada do diagrama Mermaid.
        Levanta RenderizadorMermaidError em falha.
        """
        pass
