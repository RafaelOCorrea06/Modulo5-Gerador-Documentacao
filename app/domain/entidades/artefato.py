from dataclasses import dataclass


@dataclass(frozen=True)
class Artefato:
    """
    Entidade usada pela GD-09 para representar bytes gerados por um job.

    Mantida para não quebrar a geração assíncrona/job tracking.
    """

    job_id: str
    nome: str
    mime_type: str
    conteudo: bytes

    @property
    def tamanho_bytes(self) -> int:
        return len(self.conteudo)


@dataclass(frozen=True)
class ArtefatoGerado:
    """
    Entidade usada pela GD-01 para representar um arquivo gerado
    diretamente pelo endpoint de relatórios.

    Mantida separada de Artefato porque a GD-01 retorna arquivos
    síncronos com nome_arquivo e media_type.
    """

    nome_arquivo: str
    conteudo: bytes
    media_type: str