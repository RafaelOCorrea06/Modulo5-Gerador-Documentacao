# Testes da API HTTP de matrizes (US GD-06).

import importlib

import pytest


@pytest.fixture
def cliente(monkeypatch, tmp_path):
    monkeypatch.setenv("ADAPTADOR_GITHUB", "fake")
    monkeypatch.setenv("ADAPTADOR_IA_ANALISE", "fake")
    monkeypatch.setenv("RENDERIZADOR_MERMAID", "fake")
    monkeypatch.setenv("MATRIZ_SQLITE_PATH", str(tmp_path / "matriz.db"))

    from app.config import composition_root, settings
    importlib.reload(settings)
    importlib.reload(composition_root)

    import main as main_module
    importlib.reload(main_module)
    from fastapi.testclient import TestClient
    return TestClient(main_module.app)


def test_criar_listar_obter(cliente):
    r = cliente.post("/matrizes", json={"nome": "Login", "descricao": "auth"})
    assert r.status_code == 201
    matriz = r.json()
    assert matriz["nome"] == "Login"

    r2 = cliente.get("/matrizes")
    assert r2.status_code == 200
    assert len(r2.json()["matrizes"]) == 1

    r3 = cliente.get(f"/matrizes/{matriz['id']}")
    assert r3.status_code == 200


def test_criar_sem_nome_400(cliente):
    r = cliente.post("/matrizes", json={"nome": ""})
    assert r.status_code == 400


def test_obter_inexistente_404(cliente):
    r = cliente.get("/matrizes/nao-existe")
    assert r.status_code == 404


def test_adicionar_requisito_teste_e_vincular(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "x"}).json()
    r = cliente.post(f"/matrizes/{matriz['id']}/requisitos",
                     json={"id": "REQ-001", "titulo": "Login", "prioridade": "alta"})
    assert r.status_code == 201

    r = cliente.post(f"/matrizes/{matriz['id']}/testes",
                     json={"id": "TC-01", "titulo": "test_login", "tipo": "unidade"})
    assert r.status_code == 201

    r = cliente.post(f"/matrizes/{matriz['id']}/vinculos",
                     json={"requisito_id": "REQ-001", "teste_id": "TC-01"})
    assert r.status_code == 201
    assert r.json()["nivel_cobertura"] == "completo"


def test_vinculo_duplicado_409(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "x"}).json()
    cliente.post(f"/matrizes/{matriz['id']}/requisitos",
                 json={"id": "REQ-001", "titulo": "Login"})
    cliente.post(f"/matrizes/{matriz['id']}/testes",
                 json={"id": "TC-01", "titulo": "test_login"})
    cliente.post(f"/matrizes/{matriz['id']}/vinculos",
                 json={"requisito_id": "REQ-001", "teste_id": "TC-01"})
    r = cliente.post(f"/matrizes/{matriz['id']}/vinculos",
                     json={"requisito_id": "REQ-001", "teste_id": "TC-01"})
    assert r.status_code == 409


def test_vincular_requisito_inexistente_404(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "x"}).json()
    cliente.post(f"/matrizes/{matriz['id']}/testes",
                 json={"id": "TC-01", "titulo": "t"})
    r = cliente.post(f"/matrizes/{matriz['id']}/vinculos",
                     json={"requisito_id": "REQ-X", "teste_id": "TC-01"})
    assert r.status_code == 404


def test_lacunas_devolve_estatisticas(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "x"}).json()
    cliente.post(f"/matrizes/{matriz['id']}/requisitos", json={"id": "REQ-001", "titulo": "A"})
    cliente.post(f"/matrizes/{matriz['id']}/requisitos", json={"id": "REQ-002", "titulo": "B"})
    cliente.post(f"/matrizes/{matriz['id']}/testes", json={"id": "TC-01", "titulo": "t"})
    cliente.post(f"/matrizes/{matriz['id']}/vinculos",
                 json={"requisito_id": "REQ-001", "teste_id": "TC-01"})
    r = cliente.get(f"/matrizes/{matriz['id']}/lacunas")
    assert r.status_code == 200
    body = r.json()
    assert "REQ-002" in body["requisitos_sem_teste"]
    assert body["total"] == 1


def test_exportar_markdown(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "Login"}).json()
    cliente.post(f"/matrizes/{matriz['id']}/requisitos", json={"id": "REQ-001", "titulo": "A"})
    r = cliente.get(f"/matrizes/{matriz['id']}/exportar?formato=md")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    assert "Matriz de Rastreabilidade" in r.text


def test_exportar_pdf(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "Login"}).json()
    cliente.post(f"/matrizes/{matriz['id']}/requisitos", json={"id": "REQ-001", "titulo": "A"})
    r = cliente.get(f"/matrizes/{matriz['id']}/exportar?formato=pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


def test_exportar_formato_invalido_400(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "x"}).json()
    r = cliente.get(f"/matrizes/{matriz['id']}/exportar?formato=docx")
    assert r.status_code == 400


def test_desvincular_204(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "x"}).json()
    cliente.post(f"/matrizes/{matriz['id']}/requisitos", json={"id": "REQ-001", "titulo": "A"})
    cliente.post(f"/matrizes/{matriz['id']}/testes", json={"id": "TC-01", "titulo": "t"})
    cliente.post(f"/matrizes/{matriz['id']}/vinculos",
                 json={"requisito_id": "REQ-001", "teste_id": "TC-01"})
    r = cliente.delete(f"/matrizes/{matriz['id']}/vinculos/REQ-001/TC-01")
    assert r.status_code == 204

    r = cliente.delete(f"/matrizes/{matriz['id']}/vinculos/REQ-001/TC-01")
    assert r.status_code == 404


def test_remover_matriz_204_e_404(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "x"}).json()
    r = cliente.delete(f"/matrizes/{matriz['id']}")
    assert r.status_code == 204
    r = cliente.delete(f"/matrizes/{matriz['id']}")
    assert r.status_code == 404
