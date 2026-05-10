# Entidade de dominio: Artefato (US GD-09)
# Bytes gerados por um Job — armazenados no filesystem e referenciados pelo job_id.

from dataclasses import dataclass


@dataclass(frozen=True)
class Artefato:
    job_id: str
    nome: str
    mime_type: str
    conteudo: bytes

    @property
    def tamanho_bytes(self) -> int:
        return len(self.conteudo)
