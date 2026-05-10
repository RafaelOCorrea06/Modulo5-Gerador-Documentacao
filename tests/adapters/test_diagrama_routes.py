# Testes da rota POST /diagrama/branch (US GD-03).

import importlib

import pytest


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.setenv("ADAPTADOR_GITHUB", "fake")
    monkeypatch.setenv("ADAPTADOR_IA_ANALISE", "fake")
    monkeypatch.setenv("RENDERIZADOR_MERMAID", "fake")

    from app.config import composition_root, settings
    importlib.reload(settings)
    importlib.reload(composition_root)

    import main as main_module
    importlib.reload(main_module)
    from fastapi.testclient import TestClient
    return TestClient(main_module.app)


def _configurar_pipeline(repo="o/r", branch="main", arquivo="x.py"):
    """Acessa o composition root via singleton para configurar os fakes."""
    from app.config.composition_root import CompositionRoot
    root = CompositionRoot()  # cria nova instancia — mas como ADAPTADOR_*=fake, todas viram FakeXXX
    return root


def test_post_devolve_png(cliente):
    # Configura os fakes via composition root recriado a cada chamada de rota.
    # Como o get_diagrama_service() instancia CompositionRoot a cada call, configuramos
    # via env vars + acessar o singleton da rota nao funciona. Usaremos override do FastAPI.
    from app.adapters.driving.http.diagrama_routes import get_diagrama_service
    from app.adapters.driven.clients.fonte_codigo_github import FonteCodigoFake
    from app.adapters.driven.clients.cliente_ia_analise import ClienteIAAnaliseFake
    from app.adapters.driven.renderizadores.renderizador_mermaid import RenderizadorMermaidFake
    from app.application.services.diagrama_service_impl import DiagramaServiceImpl
    import main as main_module

    fonte = FonteCodigoFake()
    fonte.configurar("o/r", "main", "x.py", "class A:\n    pass\n")
    ia = ClienteIAAnaliseFake()
    ia.configurar_resposta({"mermaid": "classDiagram\n    class A\n", "warnings": [], "linguagem": "python"})
    service = DiagramaServiceImpl(fonte_codigo=fonte, cliente_ia=ia, renderizador=RenderizadorMermaidFake())
    main_module.app.dependency_overrides[get_diagrama_service] = lambda: service

    try:
        r = cliente.post("/diagrama/branch", json={
            "repositorio": "o/r", "branch": "main", "arquivo": "x.py", "formato": "png",
        })
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/png"
        assert r.content[:2] == b"\x89P"
    finally:
        main_module.app.dependency_overrides.clear()


def test_post_devolve_svg(cliente):
    from app.adapters.driving.http.diagrama_routes import get_diagrama_service
    from app.adapters.driven.clients.fonte_codigo_github import FonteCodigoFake
    from app.adapters.driven.clients.cliente_ia_analise import ClienteIAAnaliseFake
    from app.adapters.driven.renderizadores.renderizador_mermaid import RenderizadorMermaidFake
    from app.application.services.diagrama_service_impl import DiagramaServiceImpl
    import main as main_module

    fonte = FonteCodigoFake()
    fonte.configurar("o/r", "main", "x.py", "class A:\n    pass\n")
    ia = ClienteIAAnaliseFake()
    ia.configurar_resposta({"mermaid": "classDiagram\n    class A\n", "warnings": [], "linguagem": "python"})
    service = DiagramaServiceImpl(fonte_codigo=fonte, cliente_ia=ia, renderizador=RenderizadorMermaidFake())
    main_module.app.dependency_overrides[get_diagrama_service] = lambda: service

    try:
        r = cliente.post("/diagrama/branch", json={
            "repositorio": "o/r", "branch": "main", "arquivo": "x.py", "formato": "svg",
        })
        assert r.status_code == 200
        assert "image/svg" in r.headers["content-type"]
        assert r.content.startswith(b"<svg")
    finally:
        main_module.app.dependency_overrides.clear()


def test_post_devolve_mermaid_json(cliente):
    from app.adapters.driving.http.diagrama_routes import get_diagrama_service
    from app.adapters.driven.clients.fonte_codigo_github import FonteCodigoFake
    from app.adapters.driven.clients.cliente_ia_analise import ClienteIAAnaliseFake
    from app.adapters.driven.renderizadores.renderizador_mermaid import RenderizadorMermaidFake
    from app.application.services.diagrama_service_impl import DiagramaServiceImpl
    import main as main_module

    fonte = FonteCodigoFake()
    fonte.configurar("o/r", "main", "x.py", "class A:\n    pass\n")
    ia = ClienteIAAnaliseFake()
    ia.configurar_resposta({
        "componentes": [{"nome": "A", "tipo": "classe", "metodos": [], "atributos": []}],
        "relacoes": [],
        "mermaid": "classDiagram\n    class A\n",
        "warnings": [],
        "linguagem": "python",
    })
    service = DiagramaServiceImpl(fonte_codigo=fonte, cliente_ia=ia, renderizador=RenderizadorMermaidFake())
    main_module.app.dependency_overrides[get_diagrama_service] = lambda: service

    try:
        r = cliente.post("/diagrama/branch", json={
            "repositorio": "o/r", "branch": "main", "arquivo": "x.py", "formato": "mermaid",
        })
        assert r.status_code == 200
        body = r.json()
        assert "mermaid" in body
        assert body["estrutura"]["componentes"][0]["nome"] == "A"
    finally:
        main_module.app.dependency_overrides.clear()


def test_post_repo_invalido_400(cliente):
    r = cliente.post("/diagrama/branch", json={
        "repositorio": "semslash", "branch": "main", "arquivo": "x.py", "formato": "png",
    })
    assert r.status_code == 400


def test_post_formato_invalido_400(cliente):
    r = cliente.post("/diagrama/branch", json={
        "repositorio": "o/r", "branch": "main", "arquivo": "x.py", "formato": "jpg",
    })
    assert r.status_code == 400


def test_post_path_traversal_400(cliente):
    r = cliente.post("/diagrama/branch", json={
        "repositorio": "o/r", "branch": "main", "arquivo": "../../x.py", "formato": "png",
    })
    assert r.status_code == 400


def test_post_arquivo_nao_encontrado_502(cliente):
    # Sem configurar a fonte, qualquer chamada cai em FonteCodigoIndisponivelError (404 do fake)
    r = cliente.post("/diagrama/branch", json={
        "repositorio": "o/r", "branch": "main", "arquivo": "nao-existe.py", "formato": "png",
    })
    assert r.status_code == 502
