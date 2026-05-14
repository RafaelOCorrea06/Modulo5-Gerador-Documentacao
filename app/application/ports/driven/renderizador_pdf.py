# Porta driven: RenderizadorPDF (US GD-06 — usado pra exportar matrizes)

from abc import ABC, abstractmethod

from app.domain.entidades.matriz_rastreabilidade import MatrizRastreabilidade


class RenderizadorPDF(ABC):

    @abstractmethod
    def renderizar_matriz(self, matriz: MatrizRastreabilidade) -> bytes:
        """Devolve os bytes do PDF da matriz."""
        pass
