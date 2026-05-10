# Implementacao do ApresentacaoService — orquestra o renderizador PPTX (US GD-07).

from app.application.ports.driving.apresentacao_service import ApresentacaoService
from app.application.ports.driven.renderizador_pptx import RenderizadorPPTX
from app.domain.entidades.apresentacao import Apresentacao


class ApresentacaoServiceImpl(ApresentacaoService):

    def __init__(self, renderizador: RenderizadorPPTX):
        self._renderizador = renderizador

    def gerar_pptx(self, apresentacao: Apresentacao) -> bytes:
        return self._renderizador.renderizar(apresentacao)
