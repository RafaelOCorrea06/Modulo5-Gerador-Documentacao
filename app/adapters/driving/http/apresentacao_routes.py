# Adaptador driving: rota HTTP para gerar apresentacoes PPTX (US GD-07).

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.application.ports.driving.apresentacao_service import ApresentacaoService
from app.config.composition_root import CompositionRoot
from app.domain.entidades.apresentacao import Apresentacao
from app.domain.entidades.slide import Slide, TipoSlide
from app.domain.excecoes import ApresentacaoInvalidaError, RenderizadorError


router = APIRouter(prefix="/apresentacao", tags=["Apresentacao"])


class SlideRequest(BaseModel):
    tipo: str = Field(..., description="Um de: capa, sumario, metricas, diagrama, status, proximos_passos, texto, encerramento")
    titulo: str = ""
    subtitulo: str = ""
    conteudo: Dict[str, Any] = Field(default_factory=dict)


class ApresentacaoRequest(BaseModel):
    titulo: str
    subtitulo: str = ""
    autor: str = ""
    data: str = ""
    nome_arquivo: Optional[str] = None
    slides: List[SlideRequest]


def get_apresentacao_service() -> ApresentacaoService:
    return CompositionRoot().get_apresentacao_service()


@router.post(
    "/gerar",
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": {}
            },
            "description": "Arquivo PPTX gerado.",
        },
        400: {"description": "Apresentacao invalida."},
    },
)
def gerar(
    payload: ApresentacaoRequest,
    service: ApresentacaoService = Depends(get_apresentacao_service),
):
    try:
        slides = []
        for s in payload.slides:
            try:
                tipo = TipoSlide(s.tipo)
            except ValueError:
                raise ApresentacaoInvalidaError(f"Tipo de slide desconhecido: {s.tipo}")
            slides.append(Slide(
                tipo=tipo,
                titulo=s.titulo,
                subtitulo=s.subtitulo,
                conteudo=s.conteudo,
            ))

        apres = Apresentacao(
            titulo=payload.titulo,
            subtitulo=payload.subtitulo,
            autor=payload.autor,
            data=payload.data,
            slides=slides,
        )
        bytes_pptx = service.gerar_pptx(apres)
    except ApresentacaoInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RenderizadorError as e:
        raise HTTPException(status_code=500, detail=str(e))

    nome = payload.nome_arquivo or "apresentacao.pptx"
    if not nome.lower().endswith(".pptx"):
        nome = f"{nome}.pptx"

    return Response(
        content=bytes_pptx,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )
