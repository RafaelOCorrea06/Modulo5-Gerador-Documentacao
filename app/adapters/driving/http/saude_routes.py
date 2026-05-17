import time
import importlib
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/health", tags=["Monitoramento"])


@router.get("/ready")
async def get_ready():
    """
    GD-08: Health Check de prontidão.
    Verifica libs de renderização e latência.
    """
    inicio = time.time()

    # Bibliotecas que mapeamos na arquitetura do grupo
    libs_para_checar = [
        "reportlab",
        "docx",
        "pptx",
        "matplotlib"
    ]

    status_libs = {}
    for lib in libs_para_checar:
        try:
            importlib.import_module(lib)
            status_libs[lib] = "ok"
        except ImportError:
            status_libs[lib] = "erro"

    fim = time.time()
    latencia_ms = (fim - inicio) * 1000

    # Critério: apenas todas as libs OK. A latência é medida e reportada
    # de forma informativa, mas NÃO derruba a prontidão — uma primeira
    # importação lenta (cold start) não deve marcar o serviço como "not ready".
    is_ready = all(v == "ok" for v in status_libs.values())

    resultado = {
        "status": "ready" if is_ready else "unready",
        "checks": status_libs,
        "latency_ms": round(latencia_ms, 2)
    }

    if not is_ready:
        # Se alguma lib faltar, retorna erro 503
        raise HTTPException(status_code=503, detail=resultado)

    return resultado