# Adaptador driving: rota HTTP para gerar diagrama de branch (US GD-03).

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.application.ports.driving.diagrama_service import DiagramaService
from app.config.composition_root import CompositionRoot
from app.domain.excecoes import (
    FonteCodigoIndisponivelError,
    IAAnaliseIndisponivelError,
    RenderizadorMermaidError,
    RequisicaoDiagramaInvalidaError,
)


router = APIRouter(prefix="/diagrama", tags=["Diagrama"])


def get_diagrama_service() -> DiagramaService:
    return CompositionRoot().get_diagrama_service()


class GerarDiagramaRequest(BaseModel):
    repositorio: str
    branch: str
    arquivo: str
    formato: str = "png"  # "png" | "svg" | "mermaid"


_MIMETYPES = {
    "png": "image/png",
    "svg": "image/svg+xml",
}


@router.post(
    "/branch",
    responses={
        200: {
            "description": "Imagem PNG/SVG ou JSON com mermaid puro.",
            "content": {
                "image/png": {},
                "image/svg+xml": {},
                "application/json": {},
            },
        },
        400: {"description": "Inputs invalidos."},
        502: {"description": "Falha em servico externo (GitHub, IA, mermaid.ink)."},
    },
)
def gerar_de_branch(
    payload: GerarDiagramaRequest,
    service: DiagramaService = Depends(get_diagrama_service),
):
    formato = (payload.formato or "png").lower()
    if formato not in ("png", "svg", "mermaid"):
        raise HTTPException(status_code=400, detail=f"formato '{formato}' invalido — use png, svg ou mermaid.")

    try:
        diagrama = service.gerar_de_branch(
            repositorio=payload.repositorio,
            branch=payload.branch,
            arquivo=payload.arquivo,
        )
    except RequisicaoDiagramaInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FonteCodigoIndisponivelError as e:
        raise HTTPException(status_code=502, detail=f"GitHub: {e}")
    except IAAnaliseIndisponivelError as e:
        raise HTTPException(status_code=502, detail=f"IA-Analise: {e}")

    if formato == "mermaid":
        return diagrama.to_dict()

    try:
        bytes_imagem = service.renderizar_imagem(diagrama, formato)
    except RequisicaoDiagramaInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RenderizadorMermaidError as e:
        raise HTTPException(status_code=502, detail=f"mermaid.ink: {e}")

    nome = f"{payload.repositorio.replace('/', '_')}_{payload.branch}_{payload.arquivo.replace('/', '_')}.{formato}"
    return Response(
        content=bytes_imagem,
        media_type=_MIMETYPES[formato],
        headers={"Content-Disposition": f'inline; filename="{nome}"'},
    )
