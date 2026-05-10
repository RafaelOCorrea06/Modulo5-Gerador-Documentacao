# Composition Root do Gerador-Documentacao.
# Unico lugar que conhece implementacoes concretas e injeta dependencias.

from app.adapters.driven.renderizadores.adaptador_pythonpptx import AdaptadorPythonPPTX
from app.application.services.apresentacao_service_impl import ApresentacaoServiceImpl


class CompositionRoot:

    def __init__(self):
        # Driven adapters
        self.renderizador_pptx = AdaptadorPythonPPTX()

        # Services
        self.apresentacao_service = ApresentacaoServiceImpl(self.renderizador_pptx)

    def get_apresentacao_service(self) -> ApresentacaoServiceImpl:
        return self.apresentacao_service
