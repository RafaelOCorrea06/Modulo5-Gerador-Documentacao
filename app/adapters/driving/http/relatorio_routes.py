from fastapi import APIRouter, HTTPException, Response

from app.adapters.driving.http.schemas import RelatorioRequest
from app.application.services.relatorio_service_impl import RelatorioService


router = APIRouter(
    prefix="/reports",
    tags=["Relatórios"],
)

relatorio_service = RelatorioService()


@router.get("/ping")
def ping_reports():
    """
    Rota simples para verificar se o módulo de relatórios está conectado.
    """
    return {
        "module": "reports",
        "status": "ok",
    }


@router.post("")
def gerar_relatorio(request: RelatorioRequest):
    """
    Gera um relatório técnico no formato solicitado.

    Nesta primeira etapa do GD-01, estamos implementando Markdown.
    Depois adicionaremos DOCX e PDF.
    """
    try:
        artefato = relatorio_service.gerar(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return Response(
        content=artefato.conteudo,
        media_type=artefato.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{artefato.nome_arquivo}"'
        },
    )