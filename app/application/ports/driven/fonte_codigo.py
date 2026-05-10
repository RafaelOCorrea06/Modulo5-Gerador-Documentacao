# Porta driven: FonteCodigo (US GD-03)
# Abstrai onde buscar o codigo (GitHub Contents API, GitLab, filesystem, etc).

from abc import ABC, abstractmethod


class FonteCodigo(ABC):

    @abstractmethod
    def obter_arquivo_em_branch(
        self, repositorio: str, branch: str, arquivo: str,
    ) -> str:
        """
        Devolve o conteudo do arquivo no head da branch.
        Levanta FonteCodigoIndisponivelError se falhar.
        """
        pass
