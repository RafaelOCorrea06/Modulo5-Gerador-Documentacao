from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_root_deve_indicar_servico_rodando():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "gerador-documentacao"
    assert data["status"] == "running"


def test_reports_ping_deve_indicar_modulo_ok():
    response = client.get("/reports/ping")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "reports"
    assert data["status"] == "ok"


def test_deve_gerar_relatorio_markdown_com_sucesso():
    payload = {
        "titulo": "Relatório Técnico — GD-01",
        "formato": "md",
        "subtitulo": "Primeira versão em Markdown",
        "autor": "Rafael",
        "metadados": {
            "Projeto": "Documentação Inteligente",
            "User Story": "GD-01",
        },
        "secoes": [
            {
                "titulo": "Objetivo",
                "paragrafos": [
                    "Este relatório testa a geração em Markdown.",
                    "Caracteres especiais: ação, código, integração, lambda, omega, seta.",
                ],
                "listas": [
                    [
                        "Receber JSON",
                        "Gerar Markdown",
                        "Retornar arquivo",
                    ]
                ],
                "imagens": [],
            }
        ],
    }

    response = client.post("/reports", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "attachment" in response.headers["content-disposition"]
    assert "relatorio-tecnico.md" in response.headers["content-disposition"]

    conteudo = response.content.decode("utf-8")

    assert "# Relatório Técnico — GD-01" in conteudo
    assert "## Primeira versão em Markdown" in conteudo
    assert "**Autor:** Rafael" in conteudo
    assert "## Metadados" in conteudo
    assert "- **Projeto:** Documentação Inteligente" in conteudo
    assert "## Objetivo" in conteudo
    assert "Caracteres especiais: ação, código, integração, lambda, omega, seta." in conteudo
    assert "- Receber JSON" in conteudo
    assert "- Gerar Markdown" in conteudo