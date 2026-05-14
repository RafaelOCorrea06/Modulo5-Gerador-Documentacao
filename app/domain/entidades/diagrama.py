# Entidade de dominio: Diagrama (US GD-03)
# Resultado da analise de uma branch — codigo Mermaid + estrutura JSON original.

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class Diagrama:
    """Snapshot arquitetural produzido pela IA-Analise-Codigo (IA-01)."""
    repositorio: str
    branch: str
    arquivo: str
    mermaid: str
    estrutura: Dict[str, Any]  # JSON estrutural cru (componentes, relacoes, linguagem)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repositorio": self.repositorio,
            "branch": self.branch,
            "arquivo": self.arquivo,
            "mermaid": self.mermaid,
            "estrutura": self.estrutura,
            "warnings": list(self.warnings),
        }

    def tem_componentes(self) -> bool:
        return bool((self.estrutura or {}).get("componentes"))


_FORMATOS_VALIDOS = frozenset({"png", "svg"})


def normalizar_formato(formato: str) -> str:
    f = (formato or "").strip().lower()
    if f not in _FORMATOS_VALIDOS:
        raise ValueError(f"formato invalido: '{formato}'. Use png ou svg.")
    return f
