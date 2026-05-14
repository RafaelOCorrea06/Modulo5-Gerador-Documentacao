# Entidade de dominio: Slide
# Representa um slide individual da apresentacao, com tipo + conteudo livre por tipo.

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class TipoSlide(Enum):
    CAPA = "capa"
    SUMARIO = "sumario"
    METRICAS = "metricas"
    DIAGRAMA = "diagrama"
    STATUS = "status"
    PROXIMOS_PASSOS = "proximos_passos"
    TEXTO = "texto"
    ENCERRAMENTO = "encerramento"


@dataclass
class Slide:
    tipo: TipoSlide
    titulo: str = ""
    subtitulo: str = ""
    # Conteudo varia por tipo — o renderizador conhece o esquema esperado de cada um.
    # Exemplos:
    #   METRICAS: {"itens": [{"rotulo": "Velocidade", "valor": "120%", "delta": "+5%"}, ...]}
    #   STATUS:   {"itens": [{"texto": "Backend pronto", "cor": "verde"}, ...]}
    #   DIAGRAMA: {"imagem_b64": "...", "legenda": "..."}
    #   SUMARIO/PROXIMOS_PASSOS: {"itens": ["item1", ...]}
    #   TEXTO:    {"paragrafos": ["p1", "p2", ...]}
    conteudo: Dict[str, Any] = field(default_factory=dict)
