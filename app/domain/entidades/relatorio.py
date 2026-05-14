from dataclasses import dataclass, field


@dataclass(frozen=True)
class ImagemRelatorio:
    """
    Representa uma imagem incorporada ao relatório.

    Para o GD-01, a imagem chega em Base64.
    Isso permite que ela venha dentro do próprio JSON.
    """

    nome: str
    conteudo_base64: str
    tipo_mime: str = "image/png"
    legenda: str | None = None


@dataclass(frozen=True)
class SecaoRelatorio:
    """
    Representa uma seção do relatório.

    Uma seção pode ter:
    - título;
    - parágrafos;
    - listas;
    - imagens.
    """

    titulo: str
    paragrafos: list[str] = field(default_factory=list)
    listas: list[list[str]] = field(default_factory=list)
    imagens: list[ImagemRelatorio] = field(default_factory=list)


@dataclass(frozen=True)
class RelatorioTecnico:
    """
    Representa o relatório completo dentro da aplicação.

    Essa classe não depende de FastAPI, HTTP, PDF, DOCX ou Markdown.
    Ela representa apenas os dados essenciais do relatório técnico.
    """

    titulo: str
    formato: str
    secoes: list[SecaoRelatorio]
    subtitulo: str | None = None
    autor: str | None = None
    metadados: dict[str, str] = field(default_factory=dict)