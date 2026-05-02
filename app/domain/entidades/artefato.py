from dataclasses import dataclass


@dataclass(frozen=True)
class ArtefatoGerado:
    """
    Representa um arquivo gerado pelo serviço.

    Exemplo:
    - nome_arquivo: relatorio-tecnico.md
    - conteudo: bytes do arquivo
    - media_type: tipo MIME usado na resposta HTTP
    """

    nome_arquivo: str
    conteudo: bytes
    media_type: str