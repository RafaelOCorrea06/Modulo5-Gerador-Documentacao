# Entidade de dominio: Apresentacao
# Agrupa metadados (titulo, autor, data) e a lista ordenada de slides.

from dataclasses import dataclass, field
from typing import List

from app.domain.entidades.slide import Slide


@dataclass
class Apresentacao:
    titulo: str
    subtitulo: str = ""
    autor: str = ""
    data: str = ""  # data textual livre, ex: "Maio 2026"
    slides: List[Slide] = field(default_factory=list)
