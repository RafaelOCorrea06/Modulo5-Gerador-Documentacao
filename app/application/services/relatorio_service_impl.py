from app.adapters.driven.renderizadores.adaptador_markdown_nativo import (
    AdaptadorMarkdownNativo,
)
from app.adapters.driven.renderizadores.adaptador_pythondocx import (
    AdaptadorPythonDocx,
)
from app.adapters.driven.renderizadores.adaptador_reportlab import (
    AdaptadorReportLab,
)
from app.adapters.driving.http.schemas import RelatorioRequest
from app.domain.entidades.artefato import ArtefatoGerado
from app.domain.entidades.documento import DocumentoTecnico
from app.domain.entidades.secao import ImagemRelatorio, SecaoDocumento


class RelatorioService:
    """
    Serviço de aplicação responsável por coordenar a geração do relatório.

    Ele recebe o DTO da API, transforma em entidade de domínio
    e chama o adaptador de renderização adequado.
    """

    def __init__(self) -> None:
        self.adaptador_markdown = AdaptadorMarkdownNativo()
        self.adaptador_docx = AdaptadorPythonDocx()
        self.adaptador_pdf = AdaptadorReportLab()

    def gerar(self, request: RelatorioRequest) -> ArtefatoGerado:
        documento = self._converter_request_para_documento(request)

        formato = documento.formato.lower().strip()

        if formato in {"md", "markdown"}:
            return self.adaptador_markdown.renderizar(documento)

        if formato == "docx":
            return self.adaptador_docx.renderizar(documento)

        if formato == "pdf":
            return self.adaptador_pdf.renderizar(documento)

        raise ValueError(f"Formato não suportado nesta etapa: {documento.formato}")

    def _converter_request_para_documento(
        self,
        request: RelatorioRequest,
    ) -> DocumentoTecnico:
        secoes: list[SecaoDocumento] = []

        for secao_request in request.secoes:
            imagens = [
                ImagemRelatorio(
                    nome=imagem.nome,
                    conteudo_base64=imagem.conteudo_base64,
                    tipo_mime=imagem.tipo_mime,
                    legenda=imagem.legenda,
                )
                for imagem in secao_request.imagens
            ]

            secao = SecaoDocumento(
                titulo=secao_request.titulo,
                paragrafos=secao_request.paragrafos,
                listas=secao_request.listas,
                imagens=imagens,
            )

            secoes.append(secao)

        return DocumentoTecnico(
            titulo=request.titulo,
            formato=request.formato,
            subtitulo=request.subtitulo,
            autor=request.autor,
            metadados=request.metadados,
            secoes=secoes,
        )