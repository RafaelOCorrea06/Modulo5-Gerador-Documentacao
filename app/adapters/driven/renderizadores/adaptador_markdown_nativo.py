# Renderizador Markdown nativo (US GD-06).

from app.application.ports.driven.renderizador_markdown import RenderizadorMarkdown
from app.domain.entidades.matriz_rastreabilidade import (
    MatrizRastreabilidade,
    NivelCobertura,
)


class RenderizadorMarkdownNativo(RenderizadorMarkdown):

    def renderizar_matriz(self, matriz: MatrizRastreabilidade) -> str:
        cobertura = matriz.cobertura_por_requisito()
        lacunas = matriz.calcular_lacunas()
        mapa_req = {r.id: r for r in matriz.requisitos}

        linhas = []
        linhas.append(f"# Matriz de Rastreabilidade — {matriz.nome}")
        if matriz.descricao:
            linhas.append("")
            linhas.append(matriz.descricao)
        linhas.append("")
        linhas.append(f"_Atualizada em {matriz.atualizada_em.isoformat()}_")
        linhas.append("")

        # --- Resumo ---
        linhas.append("## Resumo")
        linhas.append(f"- Requisitos: **{len(matriz.requisitos)}**")
        linhas.append(f"- Testes: **{len(matriz.testes)}**")
        linhas.append(f"- Vinculos: **{len(matriz.vinculos)}**")
        linhas.append(f"- Lacunas detectadas: **{lacunas.total()}**")
        linhas.append("")

        # --- Cobertura por requisito ---
        linhas.append("## Cobertura por Requisito")
        if not matriz.requisitos:
            linhas.append("_Nenhum requisito cadastrado._")
        else:
            linhas.append("| Requisito | Titulo | Prioridade | Testes | Status |")
            linhas.append("|---|---|---|---|---|")
            niveis = {(v.requisito_id, v.teste_id): v.nivel_cobertura for v in matriz.vinculos}
            for r in matriz.requisitos:
                testes_ids = cobertura.get(r.id, [])
                if not testes_ids:
                    status = "FALTA"
                elif r.id in lacunas.requisitos_com_cobertura_parcial:
                    status = "PARCIAL"
                else:
                    status = "OK"
                marcadores = ", ".join(
                    f"`{tid}`" + (
                        " (parcial)" if niveis.get((r.id, tid)) == NivelCobertura.PARCIAL else ""
                    )
                    for tid in testes_ids
                ) or "—"
                linhas.append(f"| `{r.id}` | {r.titulo} | {r.prioridade} | {marcadores} | **{status}** |")
        linhas.append("")

        # --- Testes ---
        linhas.append("## Testes")
        if not matriz.testes:
            linhas.append("_Nenhum teste cadastrado._")
        else:
            linhas.append("| ID | Titulo | Tipo |")
            linhas.append("|---|---|---|")
            for t in matriz.testes:
                linhas.append(f"| `{t.id}` | {t.titulo} | {t.tipo.value} |")
        linhas.append("")

        # --- Lacunas ---
        linhas.append("## Lacunas")
        if lacunas.total() == 0:
            linhas.append("Sem lacunas — cobertura completa.")
        else:
            if lacunas.requisitos_sem_teste:
                linhas.append("### Requisitos sem teste")
                for rid in lacunas.requisitos_sem_teste:
                    titulo = mapa_req[rid].titulo if rid in mapa_req else ""
                    linhas.append(f"- `{rid}` — {titulo}")
            if lacunas.requisitos_com_cobertura_parcial:
                linhas.append("")
                linhas.append("### Requisitos com cobertura parcial")
                for rid in lacunas.requisitos_com_cobertura_parcial:
                    linhas.append(f"- `{rid}`")
            if lacunas.testes_sem_requisito:
                linhas.append("")
                linhas.append("### Testes orfaos (sem requisito)")
                for tid in lacunas.testes_sem_requisito:
                    linhas.append(f"- `{tid}`")

        return "\n".join(linhas) + "\n"
