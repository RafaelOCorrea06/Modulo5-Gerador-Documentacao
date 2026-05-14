# Implementacao do JobService (US GD-09).
# Roda jobs em background usando os services existentes (apresentacao, matriz, diagrama).
# Artefatos vivem 24h por padrao; depois disso o download retorna 410 Gone.

import logging
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from app.application.ports.driven.repositorio_artefatos import RepositorioArtefatos
from app.application.ports.driven.repositorio_jobs import RepositorioJobs
from app.application.ports.driving.apresentacao_service import ApresentacaoService
from app.application.ports.driving.diagrama_service import DiagramaService
from app.application.ports.driving.job_service import JobService
from app.application.ports.driving.matriz_service import MatrizService
from app.domain.entidades.apresentacao import Apresentacao
from app.domain.entidades.artefato import Artefato
from app.domain.entidades.job import Job, StatusJob, TipoJob
from app.domain.entidades.slide import Slide, TipoSlide
from app.domain.excecoes import (
    ArtefatoExpiradoError,
    ArtefatoNaoEncontradoError,
    JobInvalidoError,
    JobNaoConcluidoError,
    JobNaoEncontradoError,
)


_logger = logging.getLogger("gerador.jobs")


class JobServiceImpl(JobService):

    def __init__(
        self,
        repositorio_jobs: RepositorioJobs,
        repositorio_artefatos: RepositorioArtefatos,
        apresentacao_service: ApresentacaoService,
        matriz_service: MatrizService,
        diagrama_service: DiagramaService,
        ttl_horas: int = 24,
    ):
        self._jobs = repositorio_jobs
        self._artefatos = repositorio_artefatos
        self._apresentacao = apresentacao_service
        self._matriz = matriz_service
        self._diagrama = diagrama_service
        self._ttl_horas = ttl_horas

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def criar(self, tipo: TipoJob, parametros: Dict[str, Any]) -> Job:
        if not isinstance(parametros, dict):
            raise JobInvalidoError("parametros deve ser um dicionario.")
        # Validacao basica por tipo: garante presenca dos campos essenciais.
        self._validar_parametros(tipo, parametros)
        job = Job(tipo=tipo, parametros=dict(parametros), ttl_horas=self._ttl_horas)
        self._jobs.salvar(job)
        return job

    def executar(self, job_id: str) -> Job:
        job = self._jobs.obter(job_id)
        if job is None:
            raise JobNaoEncontradoError(f"Job {job_id} nao existe.")
        if job.status != StatusJob.PENDENTE:
            return job  # idempotente: nao re-executa

        job_em_execucao = replace(
            job, status=StatusJob.EXECUTANDO, iniciado_em=datetime.now(timezone.utc),
        )
        self._jobs.salvar(job_em_execucao)

        try:
            artefato = self._executar_por_tipo(job_em_execucao)
        except JobInvalidoError as e:
            return self._marcar_falha(job_em_execucao, f"parametros invalidos: {e}")
        except Exception as e:
            _logger.exception("Job %s (%s) falhou", job_id, job.tipo.value)
            return self._marcar_falha(job_em_execucao, str(e))

        self._artefatos.salvar(artefato)
        concluido = replace(
            job_em_execucao,
            status=StatusJob.CONCLUIDO,
            concluido_em=datetime.now(timezone.utc),
            nome_artefato=artefato.nome,
            mime_type=artefato.mime_type,
            tamanho_bytes=artefato.tamanho_bytes,
        )
        self._jobs.salvar(concluido)
        return concluido

    def consultar(self, job_id: str) -> Job:
        job = self._jobs.obter(job_id)
        if job is None:
            raise JobNaoEncontradoError(f"Job {job_id} nao existe.")
        return job

    def listar(self, status: Optional[StatusJob] = None, limite: int = 100) -> List[Job]:
        return self._jobs.listar(status=status, limite=limite)

    def obter_artefato(self, job_id: str) -> Artefato:
        job = self.consultar(job_id)
        if job.status != StatusJob.CONCLUIDO:
            raise JobNaoConcluidoError(
                f"Job {job_id} esta {job.status.value}; download nao disponivel."
            )
        if job.expirado():
            # Limpa de uma vez — economiza disco.
            self._artefatos.remover(job.id)
            raise ArtefatoExpiradoError(
                f"URL de download expirou em {job.expira_em.isoformat()}. Recrie o job."
            )
        artefato = self._artefatos.obter(job_id)
        if artefato is None:
            raise ArtefatoNaoEncontradoError(
                f"Artefato do job {job_id} nao foi encontrado no storage."
            )
        return artefato

    def limpar_expirados(self) -> int:
        agora = datetime.now(timezone.utc)
        removidos = 0
        for job in self._jobs.listar(limite=10_000):
            if job.expirado(agora=agora):
                if self._artefatos.remover(job.id):
                    removidos += 1
        return removidos

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _marcar_falha(self, job: Job, mensagem: str) -> Job:
        falhou = replace(
            job, status=StatusJob.FALHOU,
            concluido_em=datetime.now(timezone.utc), erro=mensagem,
        )
        self._jobs.salvar(falhou)
        return falhou

    def _validar_parametros(self, tipo: TipoJob, parametros: Dict[str, Any]) -> None:
        if tipo == TipoJob.APRESENTACAO_PPTX:
            if not parametros.get("titulo"):
                raise JobInvalidoError("apresentacao_pptx exige 'titulo'.")
            slides = parametros.get("slides")
            if not isinstance(slides, list) or not slides:
                raise JobInvalidoError("apresentacao_pptx exige 'slides' nao-vazio.")
        elif tipo in (TipoJob.MATRIZ_MARKDOWN, TipoJob.MATRIZ_PDF):
            if not parametros.get("matriz_id"):
                raise JobInvalidoError(f"{tipo.value} exige 'matriz_id'.")
        elif tipo in (TipoJob.DIAGRAMA_PNG, TipoJob.DIAGRAMA_SVG):
            for campo in ("repositorio", "branch", "arquivo"):
                if not parametros.get(campo):
                    raise JobInvalidoError(f"{tipo.value} exige '{campo}'.")
        else:
            raise JobInvalidoError(f"Tipo de job nao suportado: {tipo.value}")

    def _executar_por_tipo(self, job: Job) -> Artefato:
        executores: Dict[TipoJob, Callable[[Job], Artefato]] = {
            TipoJob.APRESENTACAO_PPTX: self._executar_apresentacao,
            TipoJob.MATRIZ_MARKDOWN: self._executar_matriz_md,
            TipoJob.MATRIZ_PDF: self._executar_matriz_pdf,
            TipoJob.DIAGRAMA_PNG: self._executar_diagrama_png,
            TipoJob.DIAGRAMA_SVG: self._executar_diagrama_svg,
        }
        return executores[job.tipo](job)

    def _executar_apresentacao(self, job: Job) -> Artefato:
        params = job.parametros
        slides = []
        for s in params.get("slides", []):
            try:
                tipo_slide = TipoSlide(s.get("tipo", ""))
            except ValueError:
                raise JobInvalidoError(f"tipo de slide invalido: '{s.get('tipo')}'")
            slides.append(Slide(
                tipo=tipo_slide,
                titulo=s.get("titulo", ""),
                subtitulo=s.get("subtitulo", ""),
                conteudo=s.get("conteudo", {}) or {},
            ))
        apres = Apresentacao(
            titulo=params["titulo"],
            subtitulo=params.get("subtitulo", ""),
            autor=params.get("autor", ""),
            data=params.get("data", ""),
            slides=slides,
        )
        bytes_pptx = self._apresentacao.gerar_pptx(apres)
        nome = (params.get("nome_arquivo") or "apresentacao.pptx").strip()
        if not nome.lower().endswith(".pptx"):
            nome += ".pptx"
        return Artefato(
            job_id=job.id, nome=nome,
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            conteudo=bytes_pptx,
        )

    def _executar_matriz_md(self, job: Job) -> Artefato:
        matriz_id = job.parametros["matriz_id"]
        conteudo = self._matriz.exportar_markdown(matriz_id)
        return Artefato(
            job_id=job.id, nome=f"matriz_{matriz_id}.md",
            mime_type="text/markdown; charset=utf-8",
            conteudo=conteudo.encode("utf-8"),
        )

    def _executar_matriz_pdf(self, job: Job) -> Artefato:
        matriz_id = job.parametros["matriz_id"]
        bytes_pdf = self._matriz.exportar_pdf(matriz_id)
        return Artefato(
            job_id=job.id, nome=f"matriz_{matriz_id}.pdf",
            mime_type="application/pdf", conteudo=bytes_pdf,
        )

    def _executar_diagrama_png(self, job: Job) -> Artefato:
        return self._executar_diagrama(job, formato="png", mime="image/png")

    def _executar_diagrama_svg(self, job: Job) -> Artefato:
        return self._executar_diagrama(job, formato="svg", mime="image/svg+xml")

    def _executar_diagrama(self, job: Job, formato: str, mime: str) -> Artefato:
        params = job.parametros
        diagrama = self._diagrama.gerar_de_branch(
            repositorio=params["repositorio"],
            branch=params["branch"],
            arquivo=params["arquivo"],
        )
        bytes_imagem = self._diagrama.renderizar_imagem(diagrama, formato)
        nome = f"{params['repositorio'].replace('/', '_')}_{params['branch']}_{params['arquivo'].replace('/', '_')}.{formato}"
        return Artefato(job_id=job.id, nome=nome, mime_type=mime, conteudo=bytes_imagem)
