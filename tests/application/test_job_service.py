# Testes do JobServiceImpl (US GD-09).
# Usa adapters reais (SQLite + filesystem) com tmp_path para isolamento.

from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.driven.persistence.repositorio_artefatos_filesystem import (
    RepositorioArtefatosFilesystem,
)
from app.adapters.driven.persistence.repositorio_jobs_sqlite import (
    RepositorioJobsSQLite,
)
from app.adapters.driven.persistence.repositorio_matriz_sqlite import (
    RepositorioMatrizSQLite,
)
from app.adapters.driven.renderizadores.adaptador_markdown_nativo import (
    RenderizadorMarkdownNativo,
)
from app.adapters.driven.renderizadores.adaptador_pythonpptx import AdaptadorPythonPPTX
from app.adapters.driven.renderizadores.adaptador_reportlab import (
    RenderizadorPDFReportlab,
)
from app.application.services.apresentacao_service_impl import ApresentacaoServiceImpl
from app.application.services.diagrama_service_impl import DiagramaServiceImpl
from app.application.services.job_service_impl import JobServiceImpl
from app.application.services.matriz_service_impl import MatrizServiceImpl
from app.adapters.driven.clients.cliente_ia_analise import ClienteIAAnaliseFake
from app.adapters.driven.clients.fonte_codigo_github import FonteCodigoFake
from app.adapters.driven.renderizadores.renderizador_mermaid import RenderizadorMermaidFake
from app.domain.entidades.job import Job, StatusJob, TipoJob
from app.domain.excecoes import (
    ArtefatoExpiradoError,
    JobInvalidoError,
    JobNaoConcluidoError,
    JobNaoEncontradoError,
)


@pytest.fixture
def cenario(tmp_path):
    repo_jobs = RepositorioJobsSQLite(str(tmp_path / "jobs.db"))
    repo_art = RepositorioArtefatosFilesystem(str(tmp_path / "artefatos"))
    apres = ApresentacaoServiceImpl(AdaptadorPythonPPTX())
    fonte = FonteCodigoFake()
    ia = ClienteIAAnaliseFake()
    diagrama = DiagramaServiceImpl(fonte, ia, RenderizadorMermaidFake())
    repo_mat = RepositorioMatrizSQLite(str(tmp_path / "matriz.db"))
    matriz = MatrizServiceImpl(repo_mat, RenderizadorMarkdownNativo(), RenderizadorPDFReportlab())
    service = JobServiceImpl(
        repositorio_jobs=repo_jobs, repositorio_artefatos=repo_art,
        apresentacao_service=apres, matriz_service=matriz, diagrama_service=diagrama,
        ttl_horas=24,
    )
    yield service, fonte, ia, matriz, repo_jobs, repo_art
    repo_jobs.fechar()
    repo_mat.fechar()


def test_criar_job_devolve_pendente_e_url_com_expiracao(cenario):
    service, _, _, _, _, _ = cenario
    job = service.criar(TipoJob.MATRIZ_MARKDOWN, {"matriz_id": "qualquer"})
    assert job.status == StatusJob.PENDENTE
    assert job.expira_em > job.criado_em
    assert (job.expira_em - job.criado_em) >= timedelta(hours=23)


def test_criar_tipo_invalido_levanta(cenario):
    service, _, _, _, _, _ = cenario
    with pytest.raises(JobInvalidoError):
        service.criar(TipoJob.MATRIZ_MARKDOWN, {})  # falta matriz_id


def test_executar_apresentacao_pptx(cenario):
    service, _, _, _, _, repo_art = cenario
    job = service.criar(TipoJob.APRESENTACAO_PPTX, {
        "titulo": "Demo", "subtitulo": "Sprint",
        "slides": [{"tipo": "capa"}, {"tipo": "encerramento", "titulo": "Obrigado"}],
    })
    concluido = service.executar(job.id)
    assert concluido.status == StatusJob.CONCLUIDO
    assert concluido.mime_type.startswith("application/vnd.openxmlformats")
    artefato = service.obter_artefato(job.id)
    assert artefato.conteudo[:2] == b"PK"


def test_executar_matriz_md(cenario):
    service, _, _, matriz, _, _ = cenario
    m = matriz.criar_matriz("Login")
    matriz.adicionar_requisito(m.id, "REQ-1", "tela login")
    job = service.criar(TipoJob.MATRIZ_MARKDOWN, {"matriz_id": m.id})
    concluido = service.executar(job.id)
    assert concluido.status == StatusJob.CONCLUIDO
    artefato = service.obter_artefato(job.id)
    assert artefato.mime_type.startswith("text/markdown")
    assert b"Matriz de Rastreabilidade" in artefato.conteudo


def test_executar_matriz_pdf(cenario):
    service, _, _, matriz, _, _ = cenario
    m = matriz.criar_matriz("Login")
    job = service.criar(TipoJob.MATRIZ_PDF, {"matriz_id": m.id})
    concluido = service.executar(job.id)
    assert concluido.status == StatusJob.CONCLUIDO
    assert service.obter_artefato(job.id).conteudo[:4] == b"%PDF"


def test_executar_diagrama_png(cenario):
    service, fonte, ia, _, _, _ = cenario
    fonte.configurar("o/r", "main", "x.py", "class A:\n    pass\n")
    ia.configurar_resposta({"mermaid": "classDiagram\n    class A\n", "warnings": [], "linguagem": "python"})

    job = service.criar(TipoJob.DIAGRAMA_PNG, {
        "repositorio": "o/r", "branch": "main", "arquivo": "x.py",
    })
    concluido = service.executar(job.id)
    assert concluido.status == StatusJob.CONCLUIDO
    assert service.obter_artefato(job.id).mime_type == "image/png"


def test_executar_idempotente_em_concluido(cenario):
    service, _, _, matriz, _, _ = cenario
    m = matriz.criar_matriz("X")
    job = service.criar(TipoJob.MATRIZ_MARKDOWN, {"matriz_id": m.id})
    primeiro = service.executar(job.id)
    segundo = service.executar(job.id)
    assert primeiro.id == segundo.id
    assert primeiro.concluido_em == segundo.concluido_em


def test_executar_falha_marca_failed(cenario):
    service, _, _, _, _, _ = cenario
    # Matriz inexistente -> service de matriz vai levantar -> job falha
    job = service.criar(TipoJob.MATRIZ_MARKDOWN, {"matriz_id": "nao-existe"})
    falhou = service.executar(job.id)
    assert falhou.status == StatusJob.FALHOU
    assert "nao existe" in (falhou.erro or "").lower()


def test_obter_artefato_sem_concluir_levanta(cenario):
    service, _, _, _, _, _ = cenario
    job = service.criar(TipoJob.MATRIZ_MARKDOWN, {"matriz_id": "x"})
    with pytest.raises(JobNaoConcluidoError):
        service.obter_artefato(job.id)


def test_obter_artefato_expirado_410(cenario):
    service, _, _, matriz, repo_jobs, _ = cenario
    m = matriz.criar_matriz("X")
    job = service.criar(TipoJob.MATRIZ_MARKDOWN, {"matriz_id": m.id})
    service.executar(job.id)
    # Forca expiracao: regrava o job com criado_em antigo
    from dataclasses import replace
    antigo = repo_jobs.obter(job.id)
    repo_jobs.salvar(replace(antigo, criado_em=datetime.now(timezone.utc) - timedelta(hours=48)))
    with pytest.raises(ArtefatoExpiradoError):
        service.obter_artefato(job.id)


def test_consultar_inexistente_levanta(cenario):
    service, _, _, _, _, _ = cenario
    with pytest.raises(JobNaoEncontradoError):
        service.consultar("nao-existe")


def test_listar_filtra_por_status(cenario):
    service, _, _, matriz, _, _ = cenario
    m = matriz.criar_matriz("X")
    j1 = service.criar(TipoJob.MATRIZ_MARKDOWN, {"matriz_id": m.id})
    j2 = service.criar(TipoJob.MATRIZ_MARKDOWN, {"matriz_id": m.id})
    service.executar(j1.id)
    pendentes = service.listar(status=StatusJob.PENDENTE)
    concluidos = service.listar(status=StatusJob.CONCLUIDO)
    assert {j.id for j in pendentes} == {j2.id}
    assert {j.id for j in concluidos} == {j1.id}


def test_limpar_expirados_apaga_artefatos(cenario):
    service, _, _, matriz, repo_jobs, repo_art = cenario
    m = matriz.criar_matriz("X")
    job = service.criar(TipoJob.MATRIZ_MARKDOWN, {"matriz_id": m.id})
    service.executar(job.id)
    assert repo_art.obter(job.id) is not None

    from dataclasses import replace
    antigo = repo_jobs.obter(job.id)
    repo_jobs.salvar(replace(antigo, criado_em=datetime.now(timezone.utc) - timedelta(hours=48)))

    removidos = service.limpar_expirados()
    assert removidos == 1
    assert repo_art.obter(job.id) is None
