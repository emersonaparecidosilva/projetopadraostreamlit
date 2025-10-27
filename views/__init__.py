# --------------------------------------------------------------------------------
# __init__.py (Ponto de Entrada do Pacote 'views')
#
# Descrição:
# Este ficheiro importa todas as funções de renderização de página
# dos seus respetivos módulos, expondo-as de forma unificada para
# que o app.py possa importá-las de um único lugar.
# --------------------------------------------------------------------------------

from .home import show_home_page
from .perfil import show_perfil_page
from .setores import show_setores_page
from .gerenciamento import show_gerenciamento_page
from .permissoes import show_permissoes_page
from .logs import show_logs_page
from .personalizacao import show_personalizacao_page
from .reset import show_reset_page