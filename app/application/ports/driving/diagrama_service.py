# Porta driving: DiagramaService (US GD-03)

from abc import ABC, abstractmethod

from app.domain.entidades.diagrama import Diagrama


class DiagramaService(ABC):

    @abstractmethod
    def gerar_de_branch(
        self,
        repositorio: str,
        branch: str,
        arquivo: str,
    ) -> Diagrama:
        """Busca codigo no GitHub, manda para IA-Analise e devolve a entidade Diagrama."""
        pass

    @abstractmethod
    def renderizar_imagem(self, diagrama: Diagrama, formato: str) -> bytes:
        """Renderiza o Mermaid do diagrama em PNG ou SVG."""
        pass
