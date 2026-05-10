# Composition Root do Gerador-Documentacao.
# Unico lugar que conhece implementacoes concretas e injeta dependencias.

from app.adapters.driven.persistence.repositorio_matriz_sqlite import (
    RepositorioMatrizSQLite,
)
from app.adapters.driven.renderizadores.adaptador_markdown_nativo import (
    RenderizadorMarkdownNativo,
)
from app.adapters.driven.renderizadores.adaptador_pythonpptx import AdaptadorPythonPPTX
from app.adapters.driven.renderizadores.adaptador_reportlab import (
    RenderizadorPDFReportlab,
)
from app.adapters.driven.renderizadores.renderizador_mermaid import (
    RenderizadorMermaidFake,
    RenderizadorMermaidInk,
)
from app.adapters.driven.clients.cliente_ia_analise import (
    ClienteIAAnaliseFake,
    ClienteIAAnaliseHTTP,
)
from app.adapters.driven.clients.fonte_codigo_github import (
    FonteCodigoFake,
    FonteCodigoGitHubHTTP,
)
from app.application.services.apresentacao_service_impl import ApresentacaoServiceImpl
from app.application.services.diagrama_service_impl import DiagramaServiceImpl
from app.application.services.matriz_service_impl import MatrizServiceImpl
from app.config import settings


class CompositionRoot:

    def __init__(self):
        # Driven adapters — apresentacao (GD-07)
        self.renderizador_pptx = AdaptadorPythonPPTX()

        # Driven adapters — diagrama de branch (GD-03)
        if (settings.ADAPTADOR_GITHUB or "http").lower() == "fake":
            self.fonte_codigo = FonteCodigoFake()
        else:
            self.fonte_codigo = FonteCodigoGitHubHTTP(
                base_url=settings.GITHUB_API_BASE,
                token=settings.GITHUB_TOKEN or None,
                timeout_segundos=settings.GITHUB_TIMEOUT_S,
            )

        if (settings.ADAPTADOR_IA_ANALISE or "http").lower() == "fake":
            self.cliente_ia = ClienteIAAnaliseFake()
        else:
            self.cliente_ia = ClienteIAAnaliseHTTP(
                base_url=settings.IA_ANALISE_URL,
                timeout_segundos=settings.IA_ANALISE_TIMEOUT_S,
            )

        if (settings.RENDERIZADOR_MERMAID or "ink").lower() == "fake":
            self.renderizador_imagem = RenderizadorMermaidFake()
        else:
            self.renderizador_imagem = RenderizadorMermaidInk(
                base_url=settings.MERMAID_INK_BASE,
                timeout_segundos=settings.MERMAID_TIMEOUT_S,
            )

        # Driven adapters — matriz de rastreabilidade (GD-06)
        self.repositorio_matriz = RepositorioMatrizSQLite(settings.MATRIZ_SQLITE_PATH)
        self.renderizador_markdown = RenderizadorMarkdownNativo()
        self.renderizador_pdf = RenderizadorPDFReportlab()

        # Services
        self.apresentacao_service = ApresentacaoServiceImpl(self.renderizador_pptx)
        self.diagrama_service = DiagramaServiceImpl(
            fonte_codigo=self.fonte_codigo,
            cliente_ia=self.cliente_ia,
            renderizador=self.renderizador_imagem,
        )
        self.matriz_service = MatrizServiceImpl(
            repositorio=self.repositorio_matriz,
            renderizador_markdown=self.renderizador_markdown,
            renderizador_pdf=self.renderizador_pdf,
        )

    def get_apresentacao_service(self) -> ApresentacaoServiceImpl:
        return self.apresentacao_service

    def get_diagrama_service(self) -> DiagramaServiceImpl:
        return self.diagrama_service

    def get_matriz_service(self) -> MatrizServiceImpl:
        return self.matriz_service
