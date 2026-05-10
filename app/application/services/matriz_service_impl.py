# Implementacao do MatrizService (US GD-06).

from dataclasses import replace
from datetime import datetime, timezone
from typing import List

from app.application.ports.driven.renderizador_markdown import RenderizadorMarkdown
from app.application.ports.driven.renderizador_pdf import RenderizadorPDF
from app.application.ports.driven.repositorio_matriz import RepositorioMatriz
from app.application.ports.driving.matriz_service import MatrizService
from app.domain.entidades.matriz_rastreabilidade import (
    Lacunas,
    MatrizRastreabilidade,
    NivelCobertura,
    Requisito,
    Teste,
    TipoTeste,
    VinculoReqTeste,
)
from app.domain.excecoes import (
    ItemMatrizNaoEncontradoError,
    MatrizInvalidaError,
    MatrizNaoEncontradaError,
    VinculoMatrizDuplicadoError,
)


class MatrizServiceImpl(MatrizService):

    def __init__(
        self,
        repositorio: RepositorioMatriz,
        renderizador_markdown: RenderizadorMarkdown,
        renderizador_pdf: RenderizadorPDF,
    ):
        self._repo = repositorio
        self._md = renderizador_markdown
        self._pdf = renderizador_pdf

    # ------------------------------------------------------------------
    # Matriz
    # ------------------------------------------------------------------

    def criar_matriz(self, nome: str, descricao: str = "") -> MatrizRastreabilidade:
        if not nome or not nome.strip():
            raise MatrizInvalidaError("nome da matriz e obrigatorio.")
        matriz = MatrizRastreabilidade(nome=nome.strip(), descricao=(descricao or "").strip())
        self._repo.salvar(matriz)
        return matriz

    def obter_matriz(self, matriz_id: str) -> MatrizRastreabilidade:
        return self._exigir(matriz_id)

    def listar_matrizes(self) -> List[MatrizRastreabilidade]:
        return self._repo.listar()

    def remover_matriz(self, matriz_id: str) -> None:
        if not self._repo.remover(matriz_id):
            raise MatrizNaoEncontradaError(f"Matriz {matriz_id} nao existe.")

    # ------------------------------------------------------------------
    # Itens
    # ------------------------------------------------------------------

    def adicionar_requisito(
        self, matriz_id: str, req_id: str, titulo: str,
        descricao: str = "", prioridade: str = "media",
    ) -> Requisito:
        matriz = self._exigir(matriz_id)
        req_id = self._exigir_string("req_id", req_id)
        self._exigir_string("titulo", titulo)
        if any(r.id == req_id for r in matriz.requisitos):
            raise MatrizInvalidaError(f"Requisito '{req_id}' ja existe na matriz.")
        prioridade_n = (prioridade or "media").lower()
        if prioridade_n not in ("alta", "media", "baixa"):
            raise MatrizInvalidaError("prioridade deve ser alta, media ou baixa.")

        req = Requisito(
            id=req_id, titulo=titulo.strip(),
            descricao=(descricao or "").strip(), prioridade=prioridade_n,
        )
        matriz.requisitos.append(req)
        self._tocar(matriz)
        return req

    def adicionar_teste(
        self, matriz_id: str, teste_id: str, titulo: str,
        tipo: TipoTeste = TipoTeste.UNIDADE, descricao: str = "",
    ) -> Teste:
        matriz = self._exigir(matriz_id)
        teste_id = self._exigir_string("teste_id", teste_id)
        self._exigir_string("titulo", titulo)
        if any(t.id == teste_id for t in matriz.testes):
            raise MatrizInvalidaError(f"Teste '{teste_id}' ja existe na matriz.")

        teste = Teste(id=teste_id, titulo=titulo.strip(), tipo=tipo, descricao=(descricao or "").strip())
        matriz.testes.append(teste)
        self._tocar(matriz)
        return teste

    def vincular(
        self, matriz_id: str, req_id: str, teste_id: str,
        nivel: NivelCobertura = NivelCobertura.COMPLETO, observacao: str = "",
    ) -> VinculoReqTeste:
        matriz = self._exigir(matriz_id)
        if not any(r.id == req_id for r in matriz.requisitos):
            raise ItemMatrizNaoEncontradoError(f"Requisito '{req_id}' nao existe na matriz.")
        if not any(t.id == teste_id for t in matriz.testes):
            raise ItemMatrizNaoEncontradoError(f"Teste '{teste_id}' nao existe na matriz.")
        if any(v.requisito_id == req_id and v.teste_id == teste_id for v in matriz.vinculos):
            raise VinculoMatrizDuplicadoError(
                f"Vinculo {req_id} <-> {teste_id} ja existe."
            )

        vinculo = VinculoReqTeste(
            requisito_id=req_id, teste_id=teste_id,
            nivel_cobertura=nivel, observacao=(observacao or "").strip(),
        )
        matriz.vinculos.append(vinculo)
        self._tocar(matriz)
        return vinculo

    def desvincular(self, matriz_id: str, req_id: str, teste_id: str) -> bool:
        matriz = self._exigir(matriz_id)
        antes = len(matriz.vinculos)
        matriz.vinculos[:] = [
            v for v in matriz.vinculos
            if not (v.requisito_id == req_id and v.teste_id == teste_id)
        ]
        removeu = len(matriz.vinculos) < antes
        if removeu:
            self._tocar(matriz)
        return removeu

    # ------------------------------------------------------------------
    # Consultas e exportacao
    # ------------------------------------------------------------------

    def consultar_lacunas(self, matriz_id: str) -> Lacunas:
        return self._exigir(matriz_id).calcular_lacunas()

    def exportar_markdown(self, matriz_id: str) -> str:
        return self._md.renderizar_matriz(self._exigir(matriz_id))

    def exportar_pdf(self, matriz_id: str) -> bytes:
        return self._pdf.renderizar_matriz(self._exigir(matriz_id))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _exigir(self, matriz_id: str) -> MatrizRastreabilidade:
        if not matriz_id or not matriz_id.strip():
            raise MatrizNaoEncontradaError("matriz_id obrigatorio.")
        m = self._repo.obter(matriz_id.strip())
        if m is None:
            raise MatrizNaoEncontradaError(f"Matriz {matriz_id} nao existe.")
        return m

    @staticmethod
    def _exigir_string(nome: str, valor: str) -> str:
        if not valor or not valor.strip():
            raise MatrizInvalidaError(f"campo '{nome}' e obrigatorio.")
        return valor.strip()

    def _tocar(self, matriz: MatrizRastreabilidade) -> None:
        matriz.atualizada_em = datetime.now(timezone.utc)
        self._repo.salvar(matriz)
