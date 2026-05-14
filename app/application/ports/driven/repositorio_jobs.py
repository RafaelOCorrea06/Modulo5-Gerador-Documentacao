# Porta driven: RepositorioJobs (US GD-09)

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entidades.job import Job, StatusJob


class RepositorioJobs(ABC):

    @abstractmethod
    def salvar(self, job: Job) -> None:
        """Insere ou atualiza por id."""
        pass

    @abstractmethod
    def obter(self, job_id: str) -> Optional[Job]:
        pass

    @abstractmethod
    def listar(
        self,
        status: Optional[StatusJob] = None,
        limite: int = 100,
    ) -> List[Job]:
        pass

    @abstractmethod
    def remover(self, job_id: str) -> bool:
        pass
