# Porta driven: ClienteIAAnalise (US GD-03)
# Abstrai a comunicacao com o servico IA-Analise-Codigo (IA-01).

from abc import ABC, abstractmethod
from typing import Any, Dict


class ClienteIAAnalise(ABC):

    @abstractmethod
    def gerar_diagrama_de_codigo(self, codigo: str, tipo: str = "classe") -> Dict[str, Any]:
        """
        Chama POST /estrutura/diagrama do IA-Analise-Codigo.
        Retorna o dict cru: {componentes, relacoes, mermaid, warnings, linguagem, tipo}.
        Levanta IAAnaliseIndisponivelError em falha de rede/HTTP.
        """
        pass
