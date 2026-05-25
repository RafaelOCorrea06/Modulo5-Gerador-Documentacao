# Testes da rota GET /health/ready (US GD-08).
# Garante que a prontidao NAO falha apenas por latencia alta (primeira chamada fria).

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_ready_retorna_200_mesmo_com_latencia_alta(monkeypatch):
    """
    Mesmo que a primeira importacao das libs demore muito (latencia >> 100ms),
    o servico deve continuar 'ready' (200) — latencia e apenas informativa.
    """
    import app.adapters.driving.http.saude_routes as saude_routes

    # Simula uma medicao de latencia altissima: cada chamada a time.time()
    # avanca 5s. O handler chama duas vezes (inicio/fim) => ~5000ms >> 100ms.
    # Usamos um contador (em vez de iterador finito) porque o time.time()
    # global tambem e usado por outras libs (httpx cookiejar) apos a resposta.
    contador = {"agora": 1000.0}

    def relogio_falso():
        valor = contador["agora"]
        contador["agora"] += 5.0
        return valor

    monkeypatch.setattr(saude_routes.time, "time", relogio_falso)

    response = client.get("/health/ready")

    assert response.status_code == 200
    corpo = response.json()
    assert corpo["status"] == "ready"
    assert corpo["checks"] == {
        "reportlab": "ok",
        "docx": "ok",
        "pptx": "ok",
        "matplotlib": "ok",
    }
    assert isinstance(corpo["latency_ms"], (int, float))
    # A latencia continua sendo reportada (informativa), mesmo sendo alta.
    assert corpo["latency_ms"] >= 100


def test_ready_cold_call_retorna_200_com_libs_ok():
    """Chamada fria normal: 200, libs todas 'ok' e latency_ms numerico."""
    response = client.get("/health/ready")

    assert response.status_code == 200
    corpo = response.json()
    assert corpo["status"] == "ready"
    assert set(corpo["checks"].keys()) == {
        "reportlab",
        "docx",
        "pptx",
        "matplotlib",
    }
    assert all(v == "ok" for v in corpo["checks"].values())
    assert isinstance(corpo["latency_ms"], (int, float))
