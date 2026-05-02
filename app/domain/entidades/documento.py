from dataclasses import dataclass, field

from app.domain.entidades.secao import SecaoDocumento


@dataclass(frozen=True)
class DocumentoTecnico:
    """
    Representa o relatório técnico dentro do domínio da aplicação.

    Esta classe não depende de FastAPI, HTTP, PDF, DOCX ou Markdown.
    Ela representa apenas os dados essenciais do documento/relatório.
    """

    titulo: str
    formato: str
    secoes: list[SecaoDocumento]
    subtitulo: str | None = None
    autor: str | None = None
    metadados: dict[str, str] = field(default_factory=dict)