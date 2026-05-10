import uvicorn
from fastapi import FastAPI

from app.adapters.driving.http import saude_routes, apresentacao_routes

app = FastAPI(
    title="Geração de Documentação",
    description="Serviço de renderização de documentos e monitoramento.",
    version="1.0.0",
)

app.include_router(saude_routes.router)
app.include_router(apresentacao_routes.router)


@app.get("/")
def read_root():
    return {"message": "Serviço de Geração de Documentação Ativo"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
