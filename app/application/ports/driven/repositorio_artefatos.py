# Porta driven: RepositorioArtefatos (US GD-09)

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entidades.artefato import Artefato


class RepositorioArtefatos(ABC):

    @abstractmethod
    def salvar(self, artefato: Artefato) -> None:
        """Persiste os bytes. Sobrescreve se job_id ja existia."""
        pass

    @abstractmethod
    def obter(self, job_id: str) -> Optional[Artefato]:
        """Retorna None se nao existir (ou se foi apagado por expiracao)."""
        pass

    @abstractmethod
    def remover(self, job_id: str) -> bool:
        pass
