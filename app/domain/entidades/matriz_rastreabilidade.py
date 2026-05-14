# Entidades de dominio: MatrizRastreabilidade (US GD-06)
# Conecta requisitos a testes para auditoria de cobertura.

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Set, Tuple
import uuid


class NivelCobertura(Enum):
    COMPLETO = "completo"
    PARCIAL = "parcial"


class TipoTeste(Enum):
    UNIDADE = "unidade"
    INTEGRACAO = "integracao"
    E2E = "e2e"
    MANUAL = "manual"


@dataclass(frozen=True)
class Requisito:
    id: str             # ex: "REQ-001" (informado pelo chamador)
    titulo: str
    descricao: str = ""
    prioridade: str = "media"  # alta/media/baixa


@dataclass(frozen=True)
class Teste:
    id: str             # ex: "TC-042" ou "test_login_success"
    titulo: str
    tipo: TipoTeste = TipoTeste.UNIDADE
    descricao: str = ""


@dataclass(frozen=True)
class VinculoReqTeste:
    requisito_id: str
    teste_id: str
    nivel_cobertura: NivelCobertura = NivelCobertura.COMPLETO
    observacao: str = ""


@dataclass(frozen=True)
class Lacunas:
    """Resumo do que falta na matriz: requisitos sem teste e testes orfaos."""
    requisitos_sem_teste: Tuple[str, ...]
    testes_sem_requisito: Tuple[str, ...]
    requisitos_com_cobertura_parcial: Tuple[str, ...]

    def total(self) -> int:
        return (
            len(self.requisitos_sem_teste)
            + len(self.testes_sem_requisito)
            + len(self.requisitos_com_cobertura_parcial)
        )


@dataclass
class MatrizRastreabilidade:
    nome: str
    requisitos: List[Requisito] = field(default_factory=list)
    testes: List[Teste] = field(default_factory=list)
    vinculos: List[VinculoReqTeste] = field(default_factory=list)
    descricao: str = ""
    criada_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    atualizada_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # ------------------------------------------------------------------
    # Logica de dominio
    # ------------------------------------------------------------------

    def calcular_lacunas(self) -> Lacunas:
        ids_req_com_completo: Set[str] = {
            v.requisito_id for v in self.vinculos
            if v.nivel_cobertura == NivelCobertura.COMPLETO
        }
        ids_req_com_qualquer_vinculo: Set[str] = {v.requisito_id for v in self.vinculos}
        ids_teste_vinculados: Set[str] = {v.teste_id for v in self.vinculos}

        ids_req = [r.id for r in self.requisitos]
        ids_teste = [t.id for t in self.testes]

        sem_teste = tuple(r for r in ids_req if r not in ids_req_com_qualquer_vinculo)
        orfaos = tuple(t for t in ids_teste if t not in ids_teste_vinculados)
        parcial = tuple(
            r for r in ids_req
            if r in ids_req_com_qualquer_vinculo and r not in ids_req_com_completo
        )
        return Lacunas(
            requisitos_sem_teste=sem_teste,
            testes_sem_requisito=orfaos,
            requisitos_com_cobertura_parcial=parcial,
        )

    def cobertura_por_requisito(self) -> Dict[str, List[str]]:
        """Para cada requisito_id, lista de teste_ids que o cobrem."""
        out: Dict[str, List[str]] = {r.id: [] for r in self.requisitos}
        for v in self.vinculos:
            if v.requisito_id in out:
                out[v.requisito_id].append(v.teste_id)
        return out

    def to_dict(self) -> Dict:
        lacunas = self.calcular_lacunas()
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "criada_em": self.criada_em.isoformat(),
            "atualizada_em": self.atualizada_em.isoformat(),
            "requisitos": [
                {"id": r.id, "titulo": r.titulo, "descricao": r.descricao, "prioridade": r.prioridade}
                for r in self.requisitos
            ],
            "testes": [
                {"id": t.id, "titulo": t.titulo, "tipo": t.tipo.value, "descricao": t.descricao}
                for t in self.testes
            ],
            "vinculos": [
                {
                    "requisito_id": v.requisito_id,
                    "teste_id": v.teste_id,
                    "nivel_cobertura": v.nivel_cobertura.value,
                    "observacao": v.observacao,
                }
                for v in self.vinculos
            ],
            "lacunas": {
                "requisitos_sem_teste": list(lacunas.requisitos_sem_teste),
                "testes_sem_requisito": list(lacunas.testes_sem_requisito),
                "requisitos_com_cobertura_parcial": list(lacunas.requisitos_com_cobertura_parcial),
                "total": lacunas.total(),
            },
        }
