# Rotas HTTP para matrizes de rastreabilidade (US GD-06).

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.application.ports.driving.matriz_service import MatrizService
from app.config.composition_root import CompositionRoot
from app.domain.entidades.matriz_rastreabilidade import NivelCobertura, TipoTeste
from app.domain.excecoes import (
    ItemMatrizNaoEncontradoError,
    MatrizInvalidaError,
    MatrizNaoEncontradaError,
    RenderizadorError,
    VinculoMatrizDuplicadoError,
)


router = APIRouter(prefix="/matrizes", tags=["MatrizRastreabilidade"])


def get_matriz_service() -> MatrizService:
    return CompositionRoot().get_matriz_service()


def _parse_tipo_teste(valor: Optional[str]) -> TipoTeste:
    valor_n = (valor or "unidade").lower()
    try:
        return TipoTeste(valor_n)
    except ValueError:
        validos = ", ".join(t.value for t in TipoTeste)
        raise HTTPException(status_code=400, detail=f"tipo invalido: '{valor}'. Validos: {validos}.")


def _parse_nivel(valor: Optional[str]) -> NivelCobertura:
    valor_n = (valor or "completo").lower()
    try:
        return NivelCobertura(valor_n)
    except ValueError:
        validos = ", ".join(n.value for n in NivelCobertura)
        raise HTTPException(status_code=400, detail=f"nivel_cobertura invalido: '{valor}'. Validos: {validos}.")


# --- Pydantic ---

class CriarMatrizRequest(BaseModel):
    nome: str
    descricao: str = ""


class AdicionarRequisitoRequest(BaseModel):
    id: str
    titulo: str
    descricao: str = ""
    prioridade: str = "media"


class AdicionarTesteRequest(BaseModel):
    id: str
    titulo: str
    tipo: str = "unidade"
    descricao: str = ""


class VincularRequest(BaseModel):
    requisito_id: str
    teste_id: str
    nivel_cobertura: str = "completo"
    observacao: str = ""


# --- Rotas ---

@router.post("", status_code=201)
def criar(payload: CriarMatrizRequest, service: MatrizService = Depends(get_matriz_service)):
    try:
        m = service.criar_matriz(nome=payload.nome, descricao=payload.descricao)
    except MatrizInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return m.to_dict()


@router.get("")
def listar(service: MatrizService = Depends(get_matriz_service)):
    return {"matrizes": [m.to_dict() for m in service.listar_matrizes()]}


@router.get("/{matriz_id}")
def obter(matriz_id: str, service: MatrizService = Depends(get_matriz_service)):
    try:
        return service.obter_matriz(matriz_id).to_dict()
    except MatrizNaoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{matriz_id}", status_code=204)
def remover(matriz_id: str, service: MatrizService = Depends(get_matriz_service)):
    try:
        service.remover_matriz(matriz_id)
    except MatrizNaoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None


@router.post("/{matriz_id}/requisitos", status_code=201)
def adicionar_requisito(
    matriz_id: str,
    payload: AdicionarRequisitoRequest,
    service: MatrizService = Depends(get_matriz_service),
):
    try:
        req = service.adicionar_requisito(
            matriz_id=matriz_id, req_id=payload.id, titulo=payload.titulo,
            descricao=payload.descricao, prioridade=payload.prioridade,
        )
    except MatrizNaoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MatrizInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": req.id, "titulo": req.titulo, "descricao": req.descricao, "prioridade": req.prioridade}


@router.post("/{matriz_id}/testes", status_code=201)
def adicionar_teste(
    matriz_id: str,
    payload: AdicionarTesteRequest,
    service: MatrizService = Depends(get_matriz_service),
):
    tipo = _parse_tipo_teste(payload.tipo)
    try:
        t = service.adicionar_teste(
            matriz_id=matriz_id, teste_id=payload.id, titulo=payload.titulo,
            tipo=tipo, descricao=payload.descricao,
        )
    except MatrizNaoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MatrizInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": t.id, "titulo": t.titulo, "tipo": t.tipo.value, "descricao": t.descricao}


@router.post("/{matriz_id}/vinculos", status_code=201)
def vincular(
    matriz_id: str,
    payload: VincularRequest,
    service: MatrizService = Depends(get_matriz_service),
):
    nivel = _parse_nivel(payload.nivel_cobertura)
    try:
        v = service.vincular(
            matriz_id=matriz_id, req_id=payload.requisito_id, teste_id=payload.teste_id,
            nivel=nivel, observacao=payload.observacao,
        )
    except MatrizNaoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ItemMatrizNaoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except VinculoMatrizDuplicadoError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {
        "requisito_id": v.requisito_id, "teste_id": v.teste_id,
        "nivel_cobertura": v.nivel_cobertura.value, "observacao": v.observacao,
    }


@router.delete("/{matriz_id}/vinculos/{requisito_id}/{teste_id}", status_code=204)
def desvincular(
    matriz_id: str, requisito_id: str, teste_id: str,
    service: MatrizService = Depends(get_matriz_service),
):
    try:
        ok = service.desvincular(matriz_id, requisito_id, teste_id)
    except MatrizNaoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="vinculo nao encontrado.")
    return None


@router.get("/{matriz_id}/lacunas")
def consultar_lacunas(matriz_id: str, service: MatrizService = Depends(get_matriz_service)):
    try:
        l = service.consultar_lacunas(matriz_id)
    except MatrizNaoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "requisitos_sem_teste": list(l.requisitos_sem_teste),
        "testes_sem_requisito": list(l.testes_sem_requisito),
        "requisitos_com_cobertura_parcial": list(l.requisitos_com_cobertura_parcial),
        "total": l.total(),
    }


@router.get("/{matriz_id}/exportar")
def exportar(
    matriz_id: str,
    formato: str = "md",
    service: MatrizService = Depends(get_matriz_service),
):
    formato_n = (formato or "md").lower()
    if formato_n not in ("md", "pdf"):
        raise HTTPException(status_code=400, detail="formato deve ser 'md' ou 'pdf'.")

    try:
        if formato_n == "md":
            conteudo = service.exportar_markdown(matriz_id)
            return Response(
                content=conteudo, media_type="text/markdown; charset=utf-8",
                headers={"Content-Disposition": f'attachment; filename="matriz_{matriz_id}.md"'},
            )
        bytes_pdf = service.exportar_pdf(matriz_id)
        return Response(
            content=bytes_pdf, media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="matriz_{matriz_id}.pdf"'},
        )
    except MatrizNaoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RenderizadorError as e:
        raise HTTPException(status_code=500, detail=str(e))
