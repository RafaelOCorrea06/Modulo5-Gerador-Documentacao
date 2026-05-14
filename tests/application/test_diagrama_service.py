# Testes do DiagramaServiceImpl (US GD-03).

import pytest

from app.adapters.driven.clients.cliente_ia_analise import ClienteIAAnaliseFake
from app.adapters.driven.clients.fonte_codigo_github import FonteCodigoFake
from app.adapters.driven.renderizadores.renderizador_mermaid import RenderizadorMermaidFake
from app.application.services.diagrama_service_impl import DiagramaServiceImpl
from app.domain.excecoes import (
    FonteCodigoIndisponivelError,
    IAAnaliseIndisponivelError,
    RenderizadorMermaidError,
    RequisicaoDiagramaInvalidaError,
)


@pytest.fixture
def cenario():
    fonte = FonteCodigoFake()
    ia = ClienteIAAnaliseFake()
    rend = RenderizadorMermaidFake()
    service = DiagramaServiceImpl(fonte_codigo=fonte, cliente_ia=ia, renderizador=rend)
    return service, fonte, ia, rend


def test_pipeline_completo_devolve_diagrama(cenario):
    service, fonte, ia, _ = cenario
    fonte.configurar("o/r", "main", "app/x.py", "class A:\n    pass\n")
    ia.configurar_resposta({
        "componentes": [{"nome": "A", "tipo": "classe", "metodos": [], "atributos": []}],
        "relacoes": [],
        "mermaid": "classDiagram\n    class A\n",
        "warnings": [],
        "linguagem": "python",
    })

    diagrama = service.gerar_de_branch("o/r", "main", "app/x.py")
    assert diagrama.repositorio == "o/r"
    assert diagrama.branch == "main"
    assert diagrama.arquivo == "app/x.py"
    assert "classDiagram" in diagrama.mermaid
    assert diagrama.tem_componentes()
    assert ia.chamadas == ["class A:\n    pass\n"]


def test_repositorio_invalido_400(cenario):
    service, _, _, _ = cenario
    with pytest.raises(RequisicaoDiagramaInvalidaError):
        service.gerar_de_branch("nao_tem_barra", "main", "x.py")


def test_arquivo_com_path_traversal_falha(cenario):
    service, _, _, _ = cenario
    with pytest.raises(RequisicaoDiagramaInvalidaError):
        service.gerar_de_branch("o/r", "main", "../../etc/passwd")


def test_branch_vazia_falha(cenario):
    service, _, _, _ = cenario
    with pytest.raises(RequisicaoDiagramaInvalidaError):
        service.gerar_de_branch("o/r", "  ", "x.py")


def test_arquivo_inexistente_propaga_404(cenario):
    service, _, _, _ = cenario
    with pytest.raises(FonteCodigoIndisponivelError):
        service.gerar_de_branch("o/r", "main", "naoexiste.py")


def test_ia_indisponivel_propaga(cenario):
    service, fonte, ia, _ = cenario
    fonte.configurar("o/r", "main", "x.py", "class A: pass")
    ia.fazer_falhar_com(IAAnaliseIndisponivelError("503"))
    with pytest.raises(IAAnaliseIndisponivelError):
        service.gerar_de_branch("o/r", "main", "x.py")


def test_renderizar_png(cenario):
    service, fonte, ia, _ = cenario
    fonte.configurar("o/r", "main", "x.py", "class A:\n    pass\n")
    ia.configurar_resposta({"mermaid": "classDiagram\n    class A\n", "warnings": [], "linguagem": "python"})
    diagrama = service.gerar_de_branch("o/r", "main", "x.py")
    bytes_png = service.renderizar_imagem(diagrama, "png")
    assert bytes_png[:2] == b"\x89P"  # magic bytes de PNG (do fake)


def test_renderizar_svg(cenario):
    service, fonte, ia, _ = cenario
    fonte.configurar("o/r", "main", "x.py", "class A:\n    pass\n")
    ia.configurar_resposta({"mermaid": "classDiagram\n    class A\n", "warnings": [], "linguagem": "python"})
    diagrama = service.gerar_de_branch("o/r", "main", "x.py")
    bytes_svg = service.renderizar_imagem(diagrama, "svg")
    assert bytes_svg.startswith(b"<svg")


def test_renderizar_formato_invalido(cenario):
    service, _, _, _ = cenario
    from app.domain.entidades.diagrama import Diagrama
    diagrama = Diagrama(repositorio="o/r", branch="m", arquivo="x.py", mermaid="x", estrutura={})
    with pytest.raises(ValueError):
        service.renderizar_imagem(diagrama, "jpg")


def test_renderizar_sem_mermaid_falha(cenario):
    service, _, _, _ = cenario
    from app.domain.entidades.diagrama import Diagrama
    diagrama = Diagrama(repositorio="o/r", branch="m", arquivo="x.py", mermaid="", estrutura={})
    with pytest.raises(RequisicaoDiagramaInvalidaError):
        service.renderizar_imagem(diagrama, "png")


def test_renderizador_falha_propaga(cenario):
    service, fonte, ia, rend = cenario
    fonte.configurar("o/r", "main", "x.py", "class A:\n    pass\n")
    ia.configurar_resposta({"mermaid": "classDiagram\n    class A\n", "warnings": [], "linguagem": "python"})
    rend.fazer_falhar_com(RenderizadorMermaidError("ink fora"))
    diagrama = service.gerar_de_branch("o/r", "main", "x.py")
    with pytest.raises(RenderizadorMermaidError):
        service.renderizar_imagem(diagrama, "png")


def test_warnings_da_ia_sao_propagados(cenario):
    service, fonte, ia, _ = cenario
    fonte.configurar("o/r", "main", "x.py", "class A: pass")
    ia.configurar_resposta({
        "mermaid": "classDiagram\n",
        "warnings": ["LLM indisponivel — relacoes omitidas."],
        "linguagem": "python",
    })
    diagrama = service.gerar_de_branch("o/r", "main", "x.py")
    assert diagrama.warnings == ["LLM indisponivel — relacoes omitidas."]
