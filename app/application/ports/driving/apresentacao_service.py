# Porta driving: ApresentacaoService
# Caso de uso: gerar apresentacao PPTX de status para diretoria (US GD-07).

from abc import ABC, abstractmethod

from app.domain.entidades.apresentacao import Apresentacao


class ApresentacaoService(ABC):

    @abstractmethod
    def gerar_pptx(self, apresentacao: Apresentacao) -> bytes:
        """
        Gera os bytes do arquivo .pptx a partir da apresentacao.
        Levanta ApresentacaoInvalidaError se faltar dado obrigatorio.
        """
        pass
