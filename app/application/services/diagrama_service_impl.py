# Implementacao do DiagramaService (US GD-03).
# Pipeline: codigo (GitHub) -> Mermaid (IA-01) -> imagem (mermaid.ink).

import re

from app.application.ports.driven.cliente_ia_analise import ClienteIAAnalise
from app.application.ports.driven.fonte_codigo import FonteCodigo
from app.application.ports.driven.renderizador_imagem import RenderizadorImagem
from app.application.ports.driving.diagrama_service import DiagramaService
from app.domain.entidades.diagrama import Diagrama, normalizar_formato
from app.domain.excecoes import RequisicaoDiagramaInvalidaError


_REGEX_REPO = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
_REGEX_BRANCH = re.compile(r"^[A-Za-z0-9._/-]+$")


class DiagramaServiceImpl(DiagramaService):

    def __init__(
        self,
        fonte_codigo: FonteCodigo,
        cliente_ia: ClienteIAAnalise,
        renderizador: RenderizadorImagem,
    ):
        self._fonte = fonte_codigo
        self._ia = cliente_ia
        self._renderizador = renderizador

    def gerar_de_branch(self, repositorio: str, branch: str, arquivo: str) -> Diagrama:
        repo = self._validar_repositorio(repositorio)
        ref = self._validar_branch(branch)
        caminho = self._validar_arquivo(arquivo)

        codigo = self._fonte.obter_arquivo_em_branch(repo, ref, caminho)
        resultado = self._ia.gerar_diagrama_de_codigo(codigo)

        return Diagrama(
            repositorio=repo,
            branch=ref,
            arquivo=caminho,
            mermaid=resultado.get("mermaid", ""),
            estrutura={
                "componentes": resultado.get("componentes", []),
                "relacoes": resultado.get("relacoes", []),
                "linguagem": resultado.get("linguagem", "desconhecida"),
            },
            warnings=list(resultado.get("warnings", []) or []),
        )

    def renderizar_imagem(self, diagrama: Diagrama, formato: str) -> bytes:
        formato_n = normalizar_formato(formato)
        if not diagrama.mermaid or not diagrama.mermaid.strip():
            raise RequisicaoDiagramaInvalidaError(
                "Diagrama sem codigo Mermaid — IA-Analise nao retornou nada renderizavel."
            )
        return self._renderizador.renderizar_mermaid(diagrama.mermaid, formato_n)

    @staticmethod
    def _validar_repositorio(repo: str) -> str:
        if not repo or not repo.strip():
            raise RequisicaoDiagramaInvalidaError("repositorio e obrigatorio.")
        n = repo.strip()
        if not _REGEX_REPO.match(n):
            raise RequisicaoDiagramaInvalidaError(
                f"repositorio '{repo}' invalido. Use o formato 'owner/repo'."
            )
        return n

    @staticmethod
    def _validar_branch(branch: str) -> str:
        if not branch or not branch.strip():
            raise RequisicaoDiagramaInvalidaError("branch e obrigatorio.")
        n = branch.strip()
        if not _REGEX_BRANCH.match(n):
            raise RequisicaoDiagramaInvalidaError(
                f"branch '{branch}' contem caracteres nao suportados."
            )
        return n

    @staticmethod
    def _validar_arquivo(arquivo: str) -> str:
        if not arquivo or not arquivo.strip():
            raise RequisicaoDiagramaInvalidaError("arquivo e obrigatorio.")
        n = arquivo.strip().lstrip("/")
        if ".." in n.split("/"):
            raise RequisicaoDiagramaInvalidaError(
                f"arquivo '{arquivo}' contem '..' — nao permitido."
            )
        return n
