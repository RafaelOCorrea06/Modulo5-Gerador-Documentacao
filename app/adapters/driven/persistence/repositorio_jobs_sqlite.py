# Repositorio SQLite para jobs (US GD-09).

import json
import sqlite3
import threading
from datetime import datetime
from typing import List, Optional

from app.application.ports.driven.repositorio_jobs import RepositorioJobs
from app.domain.entidades.job import Job, StatusJob, TipoJob


_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    tipo TEXT NOT NULL,
    parametros TEXT NOT NULL,
    status TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    iniciado_em TEXT,
    concluido_em TEXT,
    erro TEXT,
    nome_artefato TEXT,
    mime_type TEXT,
    tamanho_bytes INTEGER,
    ttl_horas INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_criado ON jobs(criado_em);
"""


class RepositorioJobsSQLite(RepositorioJobs):

    def __init__(self, caminho_db: str):
        self._caminho = caminho_db
        self._conexao = sqlite3.connect(caminho_db, check_same_thread=False)
        self._conexao.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conexao.executescript(_SCHEMA)
            self._conexao.commit()

    def salvar(self, job: Job) -> None:
        sql = """
            INSERT INTO jobs (id, tipo, parametros, status, criado_em, iniciado_em,
                              concluido_em, erro, nome_artefato, mime_type,
                              tamanho_bytes, ttl_horas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = excluded.status,
                criado_em = excluded.criado_em,
                iniciado_em = excluded.iniciado_em,
                concluido_em = excluded.concluido_em,
                erro = excluded.erro,
                nome_artefato = excluded.nome_artefato,
                mime_type = excluded.mime_type,
                tamanho_bytes = excluded.tamanho_bytes
        """
        with self._lock:
            self._conexao.execute(sql, (
                job.id, job.tipo.value,
                json.dumps(job.parametros, ensure_ascii=False),
                job.status.value, job.criado_em.isoformat(),
                job.iniciado_em.isoformat() if job.iniciado_em else None,
                job.concluido_em.isoformat() if job.concluido_em else None,
                job.erro, job.nome_artefato, job.mime_type, job.tamanho_bytes,
                job.ttl_horas,
            ))
            self._conexao.commit()

    def obter(self, job_id: str) -> Optional[Job]:
        with self._lock:
            linha = self._conexao.execute(
                "SELECT * FROM jobs WHERE id = ?", (job_id,),
            ).fetchone()
        return self._linha_para_job(linha) if linha else None

    def listar(self, status: Optional[StatusJob] = None, limite: int = 100) -> List[Job]:
        clausulas: list = []
        valores: list = []
        if status is not None:
            clausulas.append("status = ?")
            valores.append(status.value)
        sql = "SELECT * FROM jobs"
        if clausulas:
            sql += " WHERE " + " AND ".join(clausulas)
        sql += " ORDER BY criado_em DESC LIMIT ?"
        valores.append(limite)
        with self._lock:
            linhas = self._conexao.execute(sql, valores).fetchall()
        return [self._linha_para_job(l) for l in linhas]

    def remover(self, job_id: str) -> bool:
        with self._lock:
            cur = self._conexao.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            self._conexao.commit()
            return cur.rowcount > 0

    def fechar(self) -> None:
        with self._lock:
            self._conexao.close()

    @staticmethod
    def _linha_para_job(linha: sqlite3.Row) -> Job:
        return Job(
            id=linha["id"],
            tipo=TipoJob(linha["tipo"]),
            parametros=json.loads(linha["parametros"]),
            status=StatusJob(linha["status"]),
            criado_em=datetime.fromisoformat(linha["criado_em"]),
            iniciado_em=datetime.fromisoformat(linha["iniciado_em"]) if linha["iniciado_em"] else None,
            concluido_em=datetime.fromisoformat(linha["concluido_em"]) if linha["concluido_em"] else None,
            erro=linha["erro"],
            nome_artefato=linha["nome_artefato"],
            mime_type=linha["mime_type"],
            tamanho_bytes=linha["tamanho_bytes"],
            ttl_horas=linha["ttl_horas"],
        )
