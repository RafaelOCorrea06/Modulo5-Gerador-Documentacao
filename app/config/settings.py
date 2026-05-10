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
