# Porta driven: RenderizadorMarkdown (US GD-06 — usado pra exportar matrizes)

from abc import ABC, abstractmethod

from app.domain.entidades.matriz_rastreabilidade import MatrizRastreabilidade


class RenderizadorMarkdown(ABC):

    @abstractmethod
    def renderizar_matriz(self, matriz: MatrizRastreabilidade) -> str:
        """Devolve a matriz em Markdown (tabelas + secao de lacunas)."""
        pass
