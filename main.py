import uvicorn
from fastapi import FastAPI
from app.adapters.driving.http import saude_routes

# 1. Instanciamos o FastAPI
app = FastAPI(
    title="Geração de Documentação",
    description="Serviço de renderização de documentos e monitoramento.",
    version="1.0.0"
)

# 2. Registramos as rotas que você acabou de criar
app.include_router(saude_routes.router)

# 3. Rota de boas-vindas para teste rápido
@app.get("/")
def read_root():
    return {"message": "Serviço de Geração de Documentação Ativo"}

# 4. Ponto de entrada para rodar via 'python main.py'
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)