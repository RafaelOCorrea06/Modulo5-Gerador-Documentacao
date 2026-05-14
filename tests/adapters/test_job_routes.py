# Testes da API HTTP de jobs assincronos (US GD-09).
# TestClient do FastAPI espera os BackgroundTasks completarem antes de devolver,
# entao por design os testes ja batem em GET /download apos o POST.

import importlib

import pytest


@pytest.fixture
def cliente(monkeypatch, tmp_path):
    monkeypatch.setenv("ADAPTADOR_GITHUB", "fake")
    monkeypatch.setenv("ADAPTADOR_IA_ANALISE", "fake")
    monkeypatch.setenv("RENDERIZADOR_MERMAID", "fake")
    monkeypatch.setenv("MATRIZ_SQLITE_PATH", str(tmp_path / "matriz.db"))
    monkeypatch.setenv("JOBS_SQLITE_PATH", str(tmp_path / "jobs.db"))
    monkeypatch.setenv("ARTEFATOS_DIR", str(tmp_path / "artefatos"))

    from app.config import composition_root, settings
    importlib.reload(settings)
    importlib.reload(composition_root)

    import main as main_module
    importlib.reload(main_module)
    from fastapi.testclient import TestClient
    return TestClient(main_module.app)


def test_post_job_pptx_executa_em_background_e_devolve_artefato(cliente):
    payload = {
        "tipo": "apresentacao_pptx",
        "parametros": {
            "titulo": "Demo", "slides": [{"tipo": "capa"}, {"tipo": "encerramento", "titulo": "Obrigado"}],
        },
    }
    r = cliente.post("/jobs", json=payload)
    assert r.status_code == 202
    body = r.json()
    # POST devolve snapshot pre-execucao — sai como pendente. Estado real eh consultado via GET.
    assert body["status"] == "pendente"
    assert "expira_em" in body

    # Background task ja rodou antes do TestClient retornar — GET reflete estado final.
    status_r = cliente.get(f"/jobs/{body['id']}")
    assert status_r.json()["status"] == "concluido"
    assert status_r.json()["url_download"].endswith("/download")

    rd = cliente.get(f"/jobs/{body['id']}/download")
    assert rd.status_code == 200
    assert rd.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert rd.content[:2] == b"PK"


def test_post_job_matriz_md_e_baixar(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "Login"}).json()
    cliente.post(f"/matrizes/{matriz['id']}/requisitos", json={"id": "REQ-1", "titulo": "x"})

    r = cliente.post("/jobs", json={"tipo": "matriz_markdown", "parametros": {"matriz_id": matriz["id"]}})
    assert r.status_code == 202
    body = r.json()

    status_r = cliente.get(f"/jobs/{body['id']}")
    assert status_r.json()["status"] == "concluido"

    rd = cliente.get(f"/jobs/{body['id']}/download")
    assert rd.status_code == 200
    assert rd.headers["content-type"].startswith("text/markdown")
    assert "Matriz de Rastreabilidade" in rd.text


def test_post_job_tipo_invalido_400(cliente):
    r = cliente.post("/jobs", json={"tipo": "tipo_que_nao_existe", "parametros": {}})
    assert r.status_code == 400


def test_post_job_parametros_faltando_400(cliente):
    r = cliente.post("/jobs", json={"tipo": "matriz_markdown", "parametros": {}})
    assert r.status_code == 400


def test_get_job_status(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "X"}).json()
    job = cliente.post("/jobs", json={
        "tipo": "matriz_markdown", "parametros": {"matriz_id": matriz["id"]},
    }).json()

    r = cliente.get(f"/jobs/{job['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == job["id"]


def test_get_job_inexistente_404(cliente):
    r = cliente.get("/jobs/nao-existe")
    assert r.status_code == 404


def test_download_de_job_falhou_devolve_409(cliente):
    # matriz_markdown com matriz inexistente -> background marca falhou
    r = cliente.post("/jobs", json={
        "tipo": "matriz_markdown", "parametros": {"matriz_id": "nao-existe-no-banco"},
    }).json()
    status_r = cliente.get(f"/jobs/{r['id']}")
    assert status_r.json()["status"] == "falhou"
    rd = cliente.get(f"/jobs/{r['id']}/download")
    assert rd.status_code == 409


def test_listar_jobs(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "X"}).json()
    cliente.post("/jobs", json={"tipo": "matriz_markdown", "parametros": {"matriz_id": matriz["id"]}})
    cliente.post("/jobs", json={"tipo": "matriz_pdf", "parametros": {"matriz_id": matriz["id"]}})
    r = cliente.get("/jobs")
    assert r.status_code == 200
    assert len(r.json()["jobs"]) >= 2


def test_listar_filtra_por_status(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "X"}).json()
    job = cliente.post("/jobs", json={"tipo": "matriz_markdown", "parametros": {"matriz_id": matriz["id"]}}).json()
    cliente.get(f"/jobs/{job['id']}")  # garante leitura pos-background
    r = cliente.get("/jobs?status=concluido")
    assert r.status_code == 200
    assert all(j["status"] == "concluido" for j in r.json()["jobs"])
    assert any(j["id"] == job["id"] for j in r.json()["jobs"])


def test_listar_status_invalido_400(cliente):
    r = cliente.get("/jobs?status=outro")
    assert r.status_code == 400


def test_response_inclui_expira_em_24h_aproximado(cliente):
    matriz = cliente.post("/matrizes", json={"nome": "X"}).json()
    job = cliente.post("/jobs", json={
        "tipo": "matriz_markdown", "parametros": {"matriz_id": matriz["id"]},
    }).json()
    from datetime import datetime
    criado = datetime.fromisoformat(job["criado_em"])
    expira = datetime.fromisoformat(job["expira_em"])
    assert (expira - criado).total_seconds() == 24 * 3600


def test_endpoint_limpar_expirados(cliente):
    r = cliente.post("/jobs/limpar-expirados")
    assert r.status_code == 200
    assert "removidos" in r.json()
