# Configuracoes do Gerador-Documentacao
# Centraliza variaveis de ambiente e identidade visual.

import os

# Identidade visual Mackenzie (US GD-07).
# Tons aproximados — substituir pelos hex oficiais da marca quando o time enviar.
COR_PRIMARIA_MACKENZIE = os.getenv("COR_PRIMARIA_MACKENZIE", "#9F1B32")  # vermelho institucional
COR_SECUNDARIA_MACKENZIE = os.getenv("COR_SECUNDARIA_MACKENZIE", "#2D2D2D")  # cinza escuro
COR_FUNDO_MACKENZIE = os.getenv("COR_FUNDO_MACKENZIE", "#F4F4F4")  # cinza claro
COR_TEXTO_MACKENZIE = os.getenv("COR_TEXTO_MACKENZIE", "#1A1A1A")  # quase preto
NOME_INSTITUICAO = os.getenv("NOME_INSTITUICAO", "Mackenzie")

# Integracao com IA-Analise-Codigo (US GD-03 / GD-05).
IA_ANALISE_URL = os.getenv("IA_ANALISE_URL", "http://localhost:8001")
IA_ANALISE_TIMEOUT_S = float(os.getenv("IA_ANALISE_TIMEOUT_S", "30.0"))
# "http" = chama o servico real; "fake" = adapter local pra testes/dev sem rede.
ADAPTADOR_IA_ANALISE = os.getenv("ADAPTADOR_IA_ANALISE", "http")

# Integracao GitHub para fetch de branches (US GD-03).
GITHUB_API_BASE = os.getenv("GITHUB_API_BASE", "https://api.github.com")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # opcional — sem token bate em rate limit anonimo
GITHUB_TIMEOUT_S = float(os.getenv("GITHUB_TIMEOUT_S", "10.0"))
ADAPTADOR_GITHUB = os.getenv("ADAPTADOR_GITHUB", "http")  # "http" | "fake"

# Renderizacao de Mermaid em imagem (US GD-03).
MERMAID_INK_BASE = os.getenv("MERMAID_INK_BASE", "https://mermaid.ink")
MERMAID_TIMEOUT_S = float(os.getenv("MERMAID_TIMEOUT_S", "20.0"))
RENDERIZADOR_MERMAID = os.getenv("RENDERIZADOR_MERMAID", "ink")  # "ink" | "fake"
