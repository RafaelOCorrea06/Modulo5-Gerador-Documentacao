# Entidade de dominio: Job (US GD-09)
# Representa uma geracao de documento que roda em background, com expiracao do download.

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid


class StatusJob(Enum):
    PENDENTE = "pendente"
    EXECUTANDO = "executando"
    CONCLUIDO = "concluido"
    FALHOU = "falhou"


class TipoJob(Enum):
    APRESENTACAO_PPTX = "apresentacao_pptx"
    MATRIZ_MARKDOWN = "matriz_markdown"
    MATRIZ_PDF = "matriz_pdf"
    DIAGRAMA_PNG = "diagrama_png"
    DIAGRAMA_SVG = "diagrama_svg"


_DURACAO_PADRAO_HORAS = 24


@dataclass(frozen=True)
class Job:
    tipo: TipoJob
    parametros: Dict[str, Any] = field(default_factory=dict)
    status: StatusJob = StatusJob.PENDENTE
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    iniciado_em: Optional[datetime] = None
    concluido_em: Optional[datetime] = None
    erro: Optional[str] = None
    nome_artefato: Optional[str] = None
    mime_type: Optional[str] = None
    tamanho_bytes: Optional[int] = None
    ttl_horas: int = _DURACAO_PADRAO_HORAS
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def expira_em(self) -> datetime:
        return self.criado_em + timedelta(hours=self.ttl_horas)

    def expirado(self, agora: Optional[datetime] = None) -> bool:
        agora = agora or datetime.now(timezone.utc)
        return agora >= self.expira_em

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tipo": self.tipo.value,
            "parametros": dict(self.parametros),
            "status": self.status.value,
            "criado_em": self.criado_em.isoformat(),
            "iniciado_em": self.iniciado_em.isoformat() if self.iniciado_em else None,
            "concluido_em": self.concluido_em.isoformat() if self.concluido_em else None,
            "expira_em": self.expira_em.isoformat(),
            "expirado": self.expirado(),
            "erro": self.erro,
            "nome_artefato": self.nome_artefato,
            "mime_type": self.mime_type,
            "tamanho_bytes": self.tamanho_bytes,
            "url_status": f"/jobs/{self.id}",
            "url_download": f"/jobs/{self.id}/download" if self.status == StatusJob.CONCLUIDO else None,
        }
