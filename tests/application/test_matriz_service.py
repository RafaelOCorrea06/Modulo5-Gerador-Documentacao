# Testes do MatrizServiceImpl com persistencia SQLite (US GD-06).

import pytest

from app.adapters.driven.persistence.repositorio_matriz_sqlite import (
    RepositorioMatrizSQLite,
)
from app.adapters.driven.renderizadores.adaptador_markdown_nativo import (
    RenderizadorMarkdownNativo,
)
from app.adapters.driven.renderizadores.adaptador_reportlab import (
    RenderizadorPDFReportlab,
)
from app.application.services.matriz_service_impl import MatrizServiceImpl
from app.domain.entidades.matriz_rastreabilidade import NivelCobertura, TipoTeste
from app.domain.excecoes import (
    ItemMatrizNaoEncontradoError,
    MatrizInvalidaError,
    MatrizNaoEncontradaError,
    VinculoMatrizDuplicadoError,
)


@pytest.fixture
def service(tmp_path):
    repo = RepositorioMatrizSQLite(str(tmp_path / "matriz.db"))
    yield MatrizServiceImpl(repo, RenderizadorMarkdownNativo(), RenderizadorPDFReportlab())
    repo.fechar()


def test_criar_matriz(service):
    m = service.criar_matriz("Login", "Modulo de autenticacao")
    assert m.nome == "Login"
    assert m.descricao == "Modulo de autenticacao"
    assert m.requisitos == []


def test_criar_sem_nome_falha(service):
    with pytest.raises(MatrizInvalidaError):
        service.criar_matriz("", "x")


def test_obter_inexistente_404(service):
    with pytest.raises(MatrizNaoEncontradaError):
        service.obter_matriz("nao-existe")


def test_adicionar_requisito_e_persistir(service):
    m = service.criar_matriz("X")
    req = service.adicionar_requisito(m.id, "REQ-001", "Login", prioridade="alta")
    assert req.id == "REQ-001"
    recuperada = service.obter_matriz(m.id)
    assert len(recuperada.requisitos) == 1
    assert recuperada.requisitos[0].prioridade == "alta"


def test_adicionar_requisito_duplicado(service):
    m = service.criar_matriz("X")
    service.adicionar_requisito(m.id, "REQ-001", "A")
    with pytest.raises(MatrizInvalidaError):
        service.adicionar_requisito(m.id, "REQ-001", "B")


def test_adicionar_requisito_prioridade_invalida(service):
    m = service.criar_matriz("X")
    with pytest.raises(MatrizInvalidaError):
        service.adicionar_requisito(m.id, "REQ-001", "Login", prioridade="urgentissima")


def test_adicionar_teste_e_vincular(service):
    m = service.criar_matriz("X")
    service.adicionar_requisito(m.id, "REQ-001", "Login")
    service.adicionar_teste(m.id, "TC-01", "test_login_ok", tipo=TipoTeste.UNIDADE)
    v = service.vincular(m.id, "REQ-001", "TC-01")
    assert v.nivel_cobertura == NivelCobertura.COMPLETO


def test_vincular_requisito_inexistente(service):
    m = service.criar_matriz("X")
    service.adicionar_teste(m.id, "TC-01", "t")
    with pytest.raises(ItemMatrizNaoEncontradoError):
        service.vincular(m.id, "REQ-X", "TC-01")


def test_vincular_teste_inexistente(service):
    m = service.criar_matriz("X")
    service.adicionar_requisito(m.id, "REQ-001", "Login")
    with pytest.raises(ItemMatrizNaoEncontradoError):
        service.vincular(m.id, "REQ-001", "TC-X")


def test_vinculo_duplicado(service):
    m = service.criar_matriz("X")
    service.adicionar_requisito(m.id, "REQ-001", "Login")
    service.adicionar_teste(m.id, "TC-01", "t")
    service.vincular(m.id, "REQ-001", "TC-01")
    with pytest.raises(VinculoMatrizDuplicadoError):
        service.vincular(m.id, "REQ-001", "TC-01")


def test_desvincular(service):
    m = service.criar_matriz("X")
    service.adicionar_requisito(m.id, "REQ-001", "Login")
    service.adicionar_teste(m.id, "TC-01", "t")
    service.vincular(m.id, "REQ-001", "TC-01")
    assert service.desvincular(m.id, "REQ-001", "TC-01") is True
    assert service.desvincular(m.id, "REQ-001", "TC-01") is False


def test_lacunas_destaca_requisitos_sem_teste_e_orfaos(service):
    m = service.criar_matriz("X")
    service.adicionar_requisito(m.id, "REQ-001", "Login")
    service.adicionar_requisito(m.id, "REQ-002", "Logout")
    service.adicionar_teste(m.id, "TC-01", "t1")
    service.adicionar_teste(m.id, "TC-02", "t2")
    service.vincular(m.id, "REQ-001", "TC-01")

    lacunas = service.consultar_lacunas(m.id)
    assert "REQ-002" in lacunas.requisitos_sem_teste
    assert "TC-02" in lacunas.testes_sem_requisito
    assert lacunas.total() == 2


def test_lacunas_inclui_cobertura_parcial(service):
    m = service.criar_matriz("X")
    service.adicionar_requisito(m.id, "REQ-001", "Login")
    service.adicionar_teste(m.id, "TC-01", "t1")
    service.vincular(m.id, "REQ-001", "TC-01", nivel=NivelCobertura.PARCIAL)
    lacunas = service.consultar_lacunas(m.id)
    assert "REQ-001" in lacunas.requisitos_com_cobertura_parcial
    assert "REQ-001" not in lacunas.requisitos_sem_teste


def test_exportar_markdown_inclui_secoes_chave(service):
    m = service.criar_matriz("Login")
    service.adicionar_requisito(m.id, "REQ-001", "Tela de login")
    service.adicionar_teste(m.id, "TC-01", "test_login_ok")
    service.vincular(m.id, "REQ-001", "TC-01")
    md = service.exportar_markdown(m.id)
    assert "# Matriz de Rastreabilidade — Login" in md
    assert "## Cobertura por Requisito" in md
    assert "REQ-001" in md and "TC-01" in md
    assert "## Lacunas" in md


def test_exportar_pdf_devolve_bytes_validos(service):
    m = service.criar_matriz("Login")
    service.adicionar_requisito(m.id, "REQ-001", "Tela de login")
    service.adicionar_teste(m.id, "TC-01", "test_login_ok")
    service.vincular(m.id, "REQ-001", "TC-01")
    pdf = service.exportar_pdf(m.id)
    assert pdf[:4] == b"%PDF"


def test_remover_matriz(service):
    m = service.criar_matriz("X")
    service.remover_matriz(m.id)
    with pytest.raises(MatrizNaoEncontradaError):
        service.obter_matriz(m.id)


def test_persiste_apos_reabrir_repositorio(tmp_path):
    caminho = str(tmp_path / "matriz.db")
    repo1 = RepositorioMatrizSQLite(caminho)
    s1 = MatrizServiceImpl(repo1, RenderizadorMarkdownNativo(), RenderizadorPDFReportlab())
    m = s1.criar_matriz("Persist")
    s1.adicionar_requisito(m.id, "REQ-001", "x")
    repo1.fechar()

    repo2 = RepositorioMatrizSQLite(caminho)
    s2 = MatrizServiceImpl(repo2, RenderizadorMarkdownNativo(), RenderizadorPDFReportlab())
    recuperada = s2.obter_matriz(m.id)
    assert len(recuperada.requisitos) == 1
    repo2.fechar()
