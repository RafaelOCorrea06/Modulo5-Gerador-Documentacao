# Porta driving: JobService (US GD-09)

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.domain.entidades.artefato import Artefato
from app.domain.entidades.job import Job, StatusJob, TipoJob


class JobService(ABC):

    @abstractmethod
    def criar(self, tipo: TipoJob, parametros: Dict[str, Any]) -> Job:
        """Cria com status PENDENTE; nao executa."""
        pass

    @abstractmethod
    def executar(self, job_id: str) -> Job:
        """Roda o trabalho real. Marca EXECUTANDO -> CONCLUIDO ou FALHOU.
        Nao levanta excecao (capturada e gravada como FALHOU)."""
        pass

    @abstractmethod
    def consultar(self, job_id: str) -> Job:
        pass

    @abstractmethod
    def listar(
        self, status: Optional[StatusJob] = None, limite: int = 100,
    ) -> List[Job]:
        pass

    @abstractmethod
    def obter_artefato(self, job_id: str) -> Artefato:
        """Levanta JobNaoConcluidoError, ArtefatoExpiradoError ou ArtefatoNaoEncontradoError."""
        pass

    @abstractmethod
    def limpar_expirados(self) -> int:
        """Apaga artefatos cujos jobs expiraram. Retorna quantos foram apagados."""
        pass
