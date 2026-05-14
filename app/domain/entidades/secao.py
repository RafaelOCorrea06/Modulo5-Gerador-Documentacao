from dataclasses import dataclass, field


@dataclass(frozen=True)
class ImagemRelatorio:
    """
    Representa uma imagem incorporada ao relatório.

    A imagem chega em Base64 para permitir que venha dentro do próprio JSON.
    """

    nome: str
    conteudo_base64: str
    tipo_mime: str = "image/png"
    legenda: str | None = None


@dataclass(frozen=True)
class SecaoDocumento:
    """
    Representa uma seção do relatório técnico.

    Cada seção pode ter:
    - título;
    - parágrafos;
    - listas;
    - imagens incorporadas.
    """

    titulo: str
    paragrafos: list[str] = field(default_factory=list)
    listas: list[list[str]] = field(default_factory=list)
    imagens: list[ImagemRelatorio] = field(default_factory=list)
