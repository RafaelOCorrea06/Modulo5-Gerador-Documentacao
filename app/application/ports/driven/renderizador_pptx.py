# Porta driven: RenderizadorPPTX
# Contrato para renderizadores de PowerPoint (.pptx) — abstrai python-pptx.

from abc import ABC, abstractmethod

from app.domain.entidades.apresentacao import Apresentacao


class RenderizadorPPTX(ABC):

    @abstractmethod
    def renderizar(self, apresentacao: Apresentacao) -> bytes:
        """Recebe a entidade Apresentacao e devolve os bytes do .pptx pronto."""
        pass
