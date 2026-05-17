import uvicorn
from fastapi import FastAPI

# Pré-aquece as libs pesadas de renderização no startup para que a
# primeira chamada de /health/ready (e a 1ª geração) não pague o custo
# de import a frio. Import guardado: se alguma faltar, o health check
# de prontidão ainda detecta via a verificação de libs existente.
try:
    import matplotlib
    matplotlib.use("Agg")  # backend não-interativo (sem GUI/servidor)
    import reportlab  # noqa: F401
    import docx  # noqa: F401
    import pptx  # noqa: F401
except ImportError:
    pass

from app.adapters.driving.http import (
    apresentacao_routes,
    diagrama_routes,
    job_routes,
    matriz_routes,
    relatorio_routes,
    saude_routes,
)

app = FastAPI(
    title="Geração de Documentação",
    description="Serviço de renderização de documentos e monitoramento.",
    version="1.0.0",
)

app.include_router(saude_routes.router)
app.include_router(apresentacao_routes.router)
app.include_router(diagrama_routes.router)
app.include_router(matriz_routes.router)
app.include_router(job_routes.router)
app.include_router(relatorio_routes.router)


@app.get("/")
def read_root():
    return {
        "message": "Serviço de Geração de Documentação Ativo",
        "service": "gerador-documentacao",
        "status": "running",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
