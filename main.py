from fastapi import FastAPI

from app.adapters.driving.http.relatorio_routes import router as relatorio_router


app = FastAPI(
    title="Gerador de Documentação",
    description="Serviço responsável por gerar relatórios técnicos em PDF, DOCX e Markdown.",
    version="0.1.0",
)

app.include_router(relatorio_router)


@app.get("/")
def root():
    return {
        "service": "gerador-documentacao",
        "status": "running",
        "docs": "/docs",
    }
