import base64
import tempfile
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

from app.domain.entidades.artefato import ArtefatoGerado
from app.domain.entidades.documento import DocumentoTecnico


class AdaptadorReportLab:
    """
    Adaptador responsável por transformar um DocumentoTecnico em PDF.

    Este adaptador usa a biblioteca ReportLab para montar o PDF.
    Ele recebe a entidade de domínio DocumentoTecnico e devolve um ArtefatoGerado.
    """

    def renderizar(self, documento: DocumentoTecnico) -> ArtefatoGerado:
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title=documento.titulo,
            author=documento.autor or "",
        )

        styles = getSampleStyleSheet()

        titulo_style = ParagraphStyle(
            name="TituloPrincipal",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            spaceAfter=18,
        )

        subtitulo_style = ParagraphStyle(
            name="Subtitulo",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            spaceAfter=12,
        )

        secao_style = ParagraphStyle(
            name="Secao",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            spaceBefore=14,
            spaceAfter=8,
        )

        paragrafo_style = ParagraphStyle(
            name="Paragrafo",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            spaceAfter=8,
        )

        legenda_style = ParagraphStyle(
            name="Legenda",
            parent=styles["Italic"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            spaceAfter=10,
        )

        elementos = []

        elementos.append(Paragraph(self._escapar_texto(documento.titulo), titulo_style))

        if documento.subtitulo:
            elementos.append(Paragraph(self._escapar_texto(documento.subtitulo), subtitulo_style))

        if documento.autor:
            elementos.append(
                Paragraph(
                    f"<b>Autor:</b> {self._escapar_texto(documento.autor)}",
                    paragrafo_style,
                )
            )

        if documento.metadados:
            elementos.append(Paragraph("Metadados", secao_style))

            itens_metadados = []

            for chave, valor in documento.metadados.items():
                texto_item = (
                    f"<b>{self._escapar_texto(chave)}:</b> "
                    f"{self._escapar_texto(valor)}"
                )
                itens_metadados.append(
                    ListItem(
                        Paragraph(texto_item, paragrafo_style),
                        leftIndent=12,
                    )
                )

            elementos.append(
                ListFlowable(
                    itens_metadados,
                    bulletType="bullet",
                    leftIndent=18,
                )
            )

        for secao in documento.secoes:
            elementos.append(Paragraph(self._escapar_texto(secao.titulo), secao_style))

            for paragrafo in secao.paragrafos:
                elementos.append(
                    Paragraph(
                        self._escapar_texto(paragrafo),
                        paragrafo_style,
                    )
                )

            for lista in secao.listas:
                itens_lista = []

                for item in lista:
                    itens_lista.append(
                        ListItem(
                            Paragraph(self._escapar_texto(item), paragrafo_style),
                            leftIndent=12,
                        )
                    )

                elementos.append(
                    ListFlowable(
                        itens_lista,
                        bulletType="bullet",
                        leftIndent=18,
                    )
                )

            for imagem in secao.imagens:
                imagem_bytes = base64.b64decode(imagem.conteudo_base64)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
                    temp_img.write(imagem_bytes)
                    caminho_temp = Path(temp_img.name)

                try:
                    elementos.append(Spacer(1, 8))
                    elementos.append(Image(str(caminho_temp), width=14 * cm, height=8 * cm))

                    if imagem.legenda:
                        elementos.append(
                            Paragraph(
                                self._escapar_texto(imagem.legenda),
                                legenda_style,
                            )
                        )
                finally:
                    caminho_temp.unlink(missing_ok=True)

        doc.build(elementos)

        conteudo_pdf = buffer.getvalue()
        buffer.close()

        return ArtefatoGerado(
            nome_arquivo="relatorio-tecnico.pdf",
            conteudo=conteudo_pdf,
            media_type="application/pdf",
        )

    def _escapar_texto(self, texto: str) -> str:
        """
        Escapa caracteres que podem ser interpretados como marcação pelo ReportLab.

        O Paragraph do ReportLab aceita uma mini linguagem parecida com HTML.
        Por isso, se o texto tiver &, < ou >, precisamos escapar.
        """
        return (
            texto.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
