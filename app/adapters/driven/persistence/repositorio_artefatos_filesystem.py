# Repositorio de artefatos em filesystem (US GD-09).
# Bytes em <ARTEFATOS_DIR>/<job_id>.bin + metadados em sidecar JSON.
# Trade-off: simples e portavel; nao serve cluster sem disco compartilhado (substituir por S3 nesse caso).

import json
import os
import threading
from typing import Optional

from app.application.ports.driven.repositorio_artefatos import RepositorioArtefatos
from app.domain.entidades.artefato import Artefato


class RepositorioArtefatosFilesystem(RepositorioArtefatos):

    def __init__(self, diretorio: str):
        self._dir = os.path.abspath(diretorio)
        self._lock = threading.Lock()
        os.makedirs(self._dir, exist_ok=True)

    def salvar(self, artefato: Artefato) -> None:
        caminho_bin = self._caminho_bin(artefato.job_id)
        caminho_meta = self._caminho_meta(artefato.job_id)
        with self._lock:
            with open(caminho_bin, "wb") as f:
                f.write(artefato.conteudo)
            with open(caminho_meta, "w", encoding="utf-8") as f:
                json.dump({"nome": artefato.nome, "mime_type": artefato.mime_type}, f)

    def obter(self, job_id: str) -> Optional[Artefato]:
        caminho_bin = self._caminho_bin(job_id)
        caminho_meta = self._caminho_meta(job_id)
        with self._lock:
            if not (os.path.exists(caminho_bin) and os.path.exists(caminho_meta)):
                return None
            with open(caminho_bin, "rb") as f:
                conteudo = f.read()
            with open(caminho_meta, "r", encoding="utf-8") as f:
                meta = json.load(f)
        return Artefato(
            job_id=job_id, nome=meta.get("nome", "artefato.bin"),
            mime_type=meta.get("mime_type", "application/octet-stream"),
            conteudo=conteudo,
        )

    def remover(self, job_id: str) -> bool:
        removeu = False
        with self._lock:
            for caminho in (self._caminho_bin(job_id), self._caminho_meta(job_id)):
                if os.path.exists(caminho):
                    os.remove(caminho)
                    removeu = True
        return removeu

    def _caminho_bin(self, job_id: str) -> str:
        return os.path.join(self._dir, f"{job_id}.bin")

    def _caminho_meta(self, job_id: str) -> str:
        return os.path.join(self._dir, f"{job_id}.json")
