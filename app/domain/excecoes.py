# Excecoes de dominio do Gerador-Documentacao


class ApresentacaoInvalidaError(ValueError):
    """Apresentacao com dados faltando ou tipo de slide nao suportado."""
    pass


class RenderizadorError(RuntimeError):
    """Falha do renderizador subjacente (ex: python-pptx)."""
    pass


class FonteCodigoIndisponivelError(RuntimeError):
    """Nao conseguimos buscar codigo do GitHub (rede, 404, rate limit)."""
    pass


class IAAnaliseIndisponivelError(RuntimeError):
    """Servico IA-Analise-Codigo nao respondeu ou retornou erro."""
    pass


class RenderizadorMermaidError(RuntimeError):
    """Falha ao renderizar Mermaid em PNG/SVG (servico mermaid.ink fora, etc)."""
    pass


class RequisicaoDiagramaInvalidaError(ValueError):
    """Inputs invalidos para gerar diagrama (repo malformado, formato desconhecido, etc)."""
    pass


class MatrizInvalidaError(ValueError):
    """Matriz de rastreabilidade com dados invalidos (campos vazios, ids duplicados, etc)."""
    pass


class MatrizNaoEncontradaError(LookupError):
    """Matriz com esse id nao existe."""
    pass


class ItemMatrizNaoEncontradoError(LookupError):
    """Requisito ou teste referenciado nao existe na matriz."""
    pass


class VinculoMatrizDuplicadoError(ValueError):
    """Esse par (requisito_id, teste_id) ja existe na matriz."""
    pass


class JobInvalidoError(ValueError):
    """Tipo de job desconhecido ou parametros faltando."""
    pass


class JobNaoEncontradoError(LookupError):
    """Job nao existe."""
    pass


class JobNaoConcluidoError(RuntimeError):
    """Tentativa de baixar artefato de job que ainda nao terminou ou que falhou."""
    pass


class ArtefatoExpiradoError(RuntimeError):
    """URL de download expirou (24h apos criacao do job)."""
    pass


class ArtefatoNaoEncontradoError(LookupError):
    """Artefato fisico nao localizado para o job (apagado ou nunca gerado)."""
    pass
