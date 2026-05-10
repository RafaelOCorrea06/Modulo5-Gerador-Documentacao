# Repositorio SQLite para matrizes de rastreabilidade (US GD-06).
# 4 tabelas: matrizes, requisitos, testes, vinculos. FK CASCADE em itens e vinculos.

import sqlite3
import threading
from datetime import datetime
from typing import List, Optional

from app.application.ports.driven.repositorio_matriz import RepositorioMatriz
from app.domain.entidades.matriz_rastreabilidade import (
    MatrizRastreabilidade,
    NivelCobertura,
    Requisito,
    Teste,
    TipoTeste,
    VinculoReqTeste,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS matrizes (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT NOT NULL DEFAULT '',
    criada_em TEXT NOT NULL,
    atualizada_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS requisitos (
    matriz_id TEXT NOT NULL,
    id TEXT NOT NULL,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL DEFAULT '',
    prioridade TEXT NOT NULL DEFAULT 'media',
    PRIMARY KEY (matriz_id, id),
    FOREIGN KEY (matriz_id) REFERENCES matrizes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS testes (
    matriz_id TEXT NOT NULL,
    id TEXT NOT NULL,
    titulo TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'unidade',
    descricao TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (matriz_id, id),
    FOREIGN KEY (matriz_id) REFERENCES matrizes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vinculos (
    matriz_id TEXT NOT NULL,
    requisito_id TEXT NOT NULL,
    teste_id TEXT NOT NULL,
    nivel_cobertura TEXT NOT NULL DEFAULT 'completo',
    observacao TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (matriz_id, requisito_id, teste_id),
    FOREIGN KEY (matriz_id) REFERENCES matrizes(id) ON DELETE CASCADE
);
"""


class RepositorioMatrizSQLite(RepositorioMatriz):

    def __init__(self, caminho_db: str):
        self._caminho = caminho_db
        self._conexao = sqlite3.connect(caminho_db, check_same_thread=False)
        self._conexao.row_factory = sqlite3.Row
        self._conexao.execute("PRAGMA foreign_keys = ON")
        self._lock = threading.Lock()
        with self._lock:
            self._conexao.executescript(_SCHEMA)
            self._conexao.commit()

    def salvar(self, matriz: MatrizRastreabilidade) -> None:
        with self._lock:
            cur = self._conexao.cursor()
            cur.execute(
                """
                INSERT INTO matrizes (id, nome, descricao, criada_em, atualizada_em)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    nome = excluded.nome,
                    descricao = excluded.descricao,
                    atualizada_em = excluded.atualizada_em
                """,
                (matriz.id, matriz.nome, matriz.descricao,
                 matriz.criada_em.isoformat(), matriz.atualizada_em.isoformat()),
            )
            # Substitui itens (mais simples que diff incremental).
            cur.execute("DELETE FROM requisitos WHERE matriz_id = ?", (matriz.id,))
            cur.execute("DELETE FROM testes WHERE matriz_id = ?", (matriz.id,))
            cur.execute("DELETE FROM vinculos WHERE matriz_id = ?", (matriz.id,))

            cur.executemany(
                "INSERT INTO requisitos (matriz_id, id, titulo, descricao, prioridade) VALUES (?, ?, ?, ?, ?)",
                [(matriz.id, r.id, r.titulo, r.descricao, r.prioridade) for r in matriz.requisitos],
            )
            cur.executemany(
                "INSERT INTO testes (matriz_id, id, titulo, tipo, descricao) VALUES (?, ?, ?, ?, ?)",
                [(matriz.id, t.id, t.titulo, t.tipo.value, t.descricao) for t in matriz.testes],
            )
            cur.executemany(
                "INSERT INTO vinculos (matriz_id, requisito_id, teste_id, nivel_cobertura, observacao) "
                "VALUES (?, ?, ?, ?, ?)",
                [(matriz.id, v.requisito_id, v.teste_id, v.nivel_cobertura.value, v.observacao)
                 for v in matriz.vinculos],
            )
            self._conexao.commit()

    def obter(self, matriz_id: str) -> Optional[MatrizRastreabilidade]:
        with self._lock:
            linha = self._conexao.execute(
                "SELECT * FROM matrizes WHERE id = ?", (matriz_id,),
            ).fetchone()
            if not linha:
                return None
            requisitos = self._conexao.execute(
                "SELECT * FROM requisitos WHERE matriz_id = ? ORDER BY id", (matriz_id,),
            ).fetchall()
            testes = self._conexao.execute(
                "SELECT * FROM testes WHERE matriz_id = ? ORDER BY id", (matriz_id,),
            ).fetchall()
            vinculos = self._conexao.execute(
                "SELECT * FROM vinculos WHERE matriz_id = ? ORDER BY requisito_id, teste_id",
                (matriz_id,),
            ).fetchall()

        return MatrizRastreabilidade(
            id=linha["id"],
            nome=linha["nome"],
            descricao=linha["descricao"] or "",
            criada_em=datetime.fromisoformat(linha["criada_em"]),
            atualizada_em=datetime.fromisoformat(linha["atualizada_em"]),
            requisitos=[
                Requisito(id=r["id"], titulo=r["titulo"], descricao=r["descricao"] or "",
                          prioridade=r["prioridade"])
                for r in requisitos
            ],
            testes=[
                Teste(id=t["id"], titulo=t["titulo"], tipo=TipoTeste(t["tipo"]),
                      descricao=t["descricao"] or "")
                for t in testes
            ],
            vinculos=[
                VinculoReqTeste(
                    requisito_id=v["requisito_id"], teste_id=v["teste_id"],
                    nivel_cobertura=NivelCobertura(v["nivel_cobertura"]),
                    observacao=v["observacao"] or "",
                ) for v in vinculos
            ],
        )

    def listar(self) -> List[MatrizRastreabilidade]:
        with self._lock:
            linhas = self._conexao.execute(
                "SELECT id FROM matrizes ORDER BY criada_em DESC",
            ).fetchall()
        ids = [linha["id"] for linha in linhas]
        return [m for m in (self.obter(i) for i in ids) if m is not None]

    def remover(self, matriz_id: str) -> bool:
        with self._lock:
            cur = self._conexao.execute("DELETE FROM matrizes WHERE id = ?", (matriz_id,))
            self._conexao.commit()
            return cur.rowcount > 0

    def fechar(self) -> None:
        with self._lock:
            self._conexao.close()
