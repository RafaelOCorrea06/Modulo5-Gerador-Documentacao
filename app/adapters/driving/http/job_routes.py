# Rotas HTTP para jobs assincronos (US GD-09).

from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.application.ports.driving.job_service import JobService
from app.config.composition_root import CompositionRoot
from app.domain.entidades.job import StatusJob, TipoJob
from app.domain.excecoes import (
    ArtefatoExpiradoError,
    ArtefatoNaoEncontradoError,
    JobInvalidoError,
    JobNaoConcluidoError,
    JobNaoEncontradoError,
)


router = APIRouter(prefix="/jobs", tags=["Jobs"])


def get_job_service() -> JobService:
    return CompositionRoot().get_job_service()


def _parse_tipo(valor: str) -> TipoJob:
    try:
        return TipoJob(valor)
    except ValueError:
        validos = ", ".join(t.value for t in TipoJob)
        raise HTTPException(status_code=400, detail=f"tipo invalido: '{valor}'. Validos: {validos}.")


def _parse_status(valor: Optional[str]) -> Optional[StatusJob]:
    if valor is None:
        return None
    try:
        return StatusJob(valor)
    except ValueError:
        validos = ", ".join(s.value for s in StatusJob)
        raise HTTPException(status_code=400, detail=f"status invalido: '{valor}'. Validos: {validos}.")


class CriarJobRequest(BaseModel):
    tipo: str = Field(..., description="apresentacao_pptx | matriz_markdown | matriz_pdf | diagrama_png | diagrama_svg")
    parametros: Dict[str, Any] = Field(default_factory=dict)


@router.post("", status_code=202)
def criar(
    payload: CriarJobRequest,
    background: BackgroundTasks,
    service: JobService = Depends(get_job_service),
):
    """
    Cria o job e responde 202 Accepted imediatamente. O processamento roda em
    background — consulte GET /jobs/{job_id} para acompanhar e GET /jobs/{job_id}/download
    para baixar quando estiver concluido. URL de download expira 24h apos a criacao.
    """
    tipo = _parse_tipo(payload.tipo)
    try:
        job = service.criar(tipo, payload.parametros)
    except JobInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))

    background.add_task(service.executar, job.id)
    return job.to_dict()


@router.get("")
def listar(
    status: Optional[str] = Query(default=None),
    limite: int = Query(default=100, ge=1, le=1000),
    service: JobService = Depends(get_job_service),
):
    status_enum = _parse_status(status)
    return {"jobs": [j.to_dict() for j in service.listar(status=status_enum, limite=limite)]}


@router.get("/{job_id}")
def consultar(job_id: str, service: JobService = Depends(get_job_service)):
    try:
        return service.consultar(job_id).to_dict()
    except JobNaoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{job_id}/download")
def baixar(job_id: str, service: JobService = Depends(get_job_service)):
    try:
        artefato = service.obter_artefato(job_id)
    except JobNaoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except JobNaoConcluidoError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ArtefatoExpiradoError as e:
        raise HTTPException(status_code=410, detail=str(e))
    except ArtefatoNaoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Response(
        content=artefato.conteudo,
        media_type=artefato.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{artefato.nome}"'},
    )


@router.post("/limpar-expirados")
def limpar_expirados(service: JobService = Depends(get_job_service)):
    removidos = service.limpar_expirados()
    return {"removidos": removidos}
