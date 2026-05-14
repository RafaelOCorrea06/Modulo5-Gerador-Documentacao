# Teste de integracao da rota POST /apresentacao/gerar (US GD-07).

import io

from fastapi.testclient import TestClient
from pptx import Presentation as AbrirPptx

from main import app


client = TestClient(app)


def test_gera_pptx_com_payload_minimo():
    payload = {
        "titulo": "Demo",
        "subtitulo": "Sprint",
        "autor": "Time",
        "data": "Maio 2026",
        "slides": [
            {"tipo": "capa"},
            {"tipo": "metricas", "titulo": "KPIs", "conteudo": {"itens": [{"rotulo": "Vel", "valor": "1.2"}]}},
            {"tipo": "encerramento", "titulo": "Obrigado"},
        ],
    }
    r = client.post("/apresentacao/gerar", json=payload)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    assert "attachment" in r.headers["content-disposition"]

    prs = AbrirPptx(io.BytesIO(r.content))
    assert len(prs.slides) == 3


def test_tipo_de_slide_invalido_retorna_400():
    payload = {"titulo": "x", "slides": [{"tipo": "tipo_que_nao_existe"}]}
    r = client.post("/apresentacao/gerar", json=payload)
    assert r.status_code == 400


def test_titulo_vazio_retorna_400():
    payload = {"titulo": "", "slides": [{"tipo": "capa"}]}
    r = client.post("/apresentacao/gerar", json=payload)
    assert r.status_code == 400
