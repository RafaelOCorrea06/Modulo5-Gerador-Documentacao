# Porta driving: MatrizService (US GD-06)

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entidades.matriz_rastreabilidade import (
    Lacunas,
    MatrizRastreabilidade,
    NivelCobertura,
    Requisito,
    Teste,
    TipoTeste,
    VinculoReqTeste,
)


class MatrizService(ABC):

    @abstractmethod
    def criar_matriz(self, nome: str, descricao: str = "") -> MatrizRastreabilidade:
        pass

    @abstractmethod
    def obter_matriz(self, matriz_id: str) -> MatrizRastreabilidade:
        pass

    @abstractmethod
    def listar_matrizes(self) -> List[MatrizRastreabilidade]:
        pass

    @abstractmethod
    def remover_matriz(self, matriz_id: str) -> None:
        pass

    @abstractmethod
    def adicionar_requisito(
        self, matriz_id: str, req_id: str, titulo: str,
        descricao: str = "", prioridade: str = "media",
    ) -> Requisito:
        pass

    @abstractmethod
    def adicionar_teste(
        self, matriz_id: str, teste_id: str, titulo: str,
        tipo: TipoTeste = TipoTeste.UNIDADE, descricao: str = "",
    ) -> Teste:
        pass

    @abstractmethod
    def vincular(
        self, matriz_id: str, req_id: str, teste_id: str,
        nivel: NivelCobertura = NivelCobertura.COMPLETO, observacao: str = "",
    ) -> VinculoReqTeste:
        pass

    @abstractmethod
    def desvincular(self, matriz_id: str, req_id: str, teste_id: str) -> bool:
        pass

    @abstractmethod
    def consultar_lacunas(self, matriz_id: str) -> Lacunas:
        pass

    @abstractmethod
    def exportar_markdown(self, matriz_id: str) -> str:
        pass

    @abstractmethod
    def exportar_pdf(self, matriz_id: str) -> bytes:
        pass
