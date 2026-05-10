# Porta driven: RepositorioMatriz (US GD-06)

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entidades.matriz_rastreabilidade import MatrizRastreabilidade


class RepositorioMatriz(ABC):

    @abstractmethod
    def salvar(self, matriz: MatrizRastreabilidade) -> None:
        """Insere ou substitui (upsert por id)."""
        pass

    @abstractmethod
    def obter(self, matriz_id: str) -> Optional[MatrizRastreabilidade]:
        pass

    @abstractmethod
    def listar(self) -> List[MatrizRastreabilidade]:
        pass

    @abstractmethod
    def remover(self, matriz_id: str) -> bool:
        pass
