# Excecoes de dominio do Gerador-Documentacao


class ApresentacaoInvalidaError(ValueError):
    """Apresentacao com dados faltando ou tipo de slide nao suportado."""
    pass


class RenderizadorError(RuntimeError):
    """Falha do renderizador subjacente (ex: python-pptx)."""
    pass
