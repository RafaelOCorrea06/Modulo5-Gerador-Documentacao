from app.domain.entidades.artefato import ArtefatoGerado
from app.domain.entidades.documento import DocumentoTecnico


class AdaptadorMarkdownNativo:
    """
    Adaptador responsável por transformar um DocumentoTecnico em Markdown.

    Ele é chamado de 'nativo' porque não depende de biblioteca externa
    para montar o conteúdo Markdown.
    """

    def renderizar(self, documento: DocumentoTecnico) -> ArtefatoGerado:
        linhas: list[str] = []

        linhas.append(f"# {documento.titulo}")
        linhas.append("")

        if documento.subtitulo:
            linhas.append(f"## {documento.subtitulo}")
            linhas.append("")

        if documento.autor:
            linhas.append(f"**Autor:** {documento.autor}")
            linhas.append("")

        if documento.metadados:
            linhas.append("## Metadados")
            linhas.append("")

            for chave, valor in documento.metadados.items():
                linhas.append(f"- **{chave}:** {valor}")

            linhas.append("")

        for secao in documento.secoes:
            linhas.append(f"## {secao.titulo}")
            linhas.append("")

            for paragrafo in secao.paragrafos:
                linhas.append(paragrafo)
                linhas.append("")

            for lista in secao.listas:
                for item in lista:
                    linhas.append(f"- {item}")
                linhas.append("")

            for imagem in secao.imagens:
                texto_alt = imagem.legenda or imagem.nome

                linhas.append(
                    f"![{texto_alt}]"
                    f"(data:{imagem.tipo_mime};base64,{imagem.conteudo_base64})"
                )

                if imagem.legenda:
                    linhas.append("")
                    linhas.append(f"*{imagem.legenda}*")

                linhas.append("")

        conteudo_markdown = "\n".join(linhas).strip() + "\n"

        return ArtefatoGerado(
            nome_arquivo="relatorio-tecnico.md",
            conteudo=conteudo_markdown.encode("utf-8"),
            media_type="text/markdown; charset=utf-8",
        )