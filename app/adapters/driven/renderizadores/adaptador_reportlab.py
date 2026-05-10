# Renderizador PDF via reportlab (US GD-06).

import io
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from app.application.ports.driven.renderizador_pdf import RenderizadorPDF
from app.domain.entidades.matriz_rastreabilidade import (
    MatrizRastreabilidade,
    NivelCobertura,
)
from app.domain.excecoes import RenderizadorError


_VERMELHO_MACKENZIE = colors.HexColor("#9F1B32")
_CINZA_LEVE = colors.HexColor("#F4F4F4")


class RenderizadorPDFReportlab(RenderizadorPDF):

    def renderizar_matriz(self, matriz: MatrizRastreabilidade) -> bytes:
        try:
            return self._renderizar(matriz)
        except RenderizadorError:
            raise
        except Exception as e:
            raise RenderizadorError(f"falha no reportlab: {e}") from e

    def _renderizar(self, matriz: MatrizRastreabilidade) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
            title=f"Matriz {matriz.nome}",
        )
        styles = getSampleStyleSheet()
        titulo_style = ParagraphStyle(
            "Titulo", parent=styles["Heading1"],
            textColor=_VERMELHO_MACKENZIE, spaceAfter=12,
        )
        h2_style = ParagraphStyle(
            "H2", parent=styles["Heading2"],
            textColor=_VERMELHO_MACKENZIE, spaceBefore=14, spaceAfter=6,
        )
        normal = styles["BodyText"]

        story = []
        story.append(Paragraph(f"Matriz de Rastreabilidade — {matriz.nome}", titulo_style))
        if matriz.descricao:
            story.append(Paragraph(matriz.descricao, normal))
        story.append(Paragraph(f"<i>Atualizada em {matriz.atualizada_em.isoformat()}</i>", normal))
        story.append(Spacer(1, 0.5 * cm))

        # Resumo
        lacunas = matriz.calcular_lacunas()
        story.append(Paragraph("Resumo", h2_style))
        resumo_dados = [
            ["Requisitos", str(len(matriz.requisitos))],
            ["Testes", str(len(matriz.testes))],
            ["Vinculos", str(len(matriz.vinculos))],
            ["Lacunas detectadas", str(lacunas.total())],
        ]
        resumo_tabela = Table(resumo_dados, colWidths=[6 * cm, 3 * cm])
        resumo_tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), _CINZA_LEVE),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(resumo_tabela)

        # Cobertura por requisito
        story.append(Paragraph("Cobertura por Requisito", h2_style))
        story.append(self._tabela_cobertura(matriz, lacunas))

        # Lacunas
        if lacunas.total() > 0:
            story.append(Paragraph("Lacunas", h2_style))
            if lacunas.requisitos_sem_teste:
                story.append(Paragraph("<b>Requisitos sem teste:</b>", normal))
                for rid in lacunas.requisitos_sem_teste:
                    story.append(Paragraph(f"- {rid}", normal))
            if lacunas.requisitos_com_cobertura_parcial:
                story.append(Paragraph("<b>Cobertura parcial:</b>", normal))
                for rid in lacunas.requisitos_com_cobertura_parcial:
                    story.append(Paragraph(f"- {rid}", normal))
            if lacunas.testes_sem_requisito:
                story.append(Paragraph("<b>Testes orfaos:</b>", normal))
                for tid in lacunas.testes_sem_requisito:
                    story.append(Paragraph(f"- {tid}", normal))

        doc.build(story)
        return buffer.getvalue()

    def _tabela_cobertura(self, matriz: MatrizRastreabilidade, lacunas) -> Table:
        cobertura = matriz.cobertura_por_requisito()
        niveis = {(v.requisito_id, v.teste_id): v.nivel_cobertura for v in matriz.vinculos}
        cabecalho = ["Requisito", "Titulo", "Prio", "Testes", "Status"]
        dados: List[List[str]] = [cabecalho]

        for r in matriz.requisitos:
            testes_ids = cobertura.get(r.id, [])
            if not testes_ids:
                status = "FALTA"
            elif r.id in lacunas.requisitos_com_cobertura_parcial:
                status = "PARCIAL"
            else:
                status = "OK"
            marcadores = ", ".join(
                tid + ("*" if niveis.get((r.id, tid)) == NivelCobertura.PARCIAL else "")
                for tid in testes_ids
            ) or "—"
            dados.append([r.id, r.titulo, r.prioridade, marcadores, status])

        if len(dados) == 1:
            dados.append(["—", "Nenhum requisito cadastrado.", "—", "—", "—"])

        tabela = Table(dados, colWidths=[3 * cm, 5 * cm, 1.5 * cm, 5 * cm, 2 * cm])
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _VERMELHO_MACKENZIE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        return tabela
