# --------------------------------------------------------------------------------
# ipp_utils.py (Módulo de Utilitários IPP)
#
# Autor: Emerson A. Silva
# Data: 20/10/2025
#
# Descrição:
# Versão final compatível com impressoras a laser (toner) e a
# jato de tinta (ink), tornando a deteção de suprimentos mais robusta.
# --------------------------------------------------------------------------------

import asyncio
from pyipp import IPP, Printer
import re

def _normalize_color(marker):
    """Função interna para padronizar os nomes de cor dos suprimentos para o banco de dados."""
    name = marker.name.lower()
    color_hex = marker.color.lower() if marker.color else ""

    # Retorna o nome da coluna no banco de dados
    if color_hex == "#000000": return "toner_preto"
    if color_hex == "#00ffff": return "toner_ciano"
    if color_hex == "#ff00ff": return "toner_magenta"
    if color_hex == "#ffff00": return "toner_amarelo"

    if re.search(r"\b(bk|black|preto)\b", name): return "toner_preto"
    if re.search(r"\b(c|cyan|ciano)\b", name): return "toner_ciano"
    if re.search(r"\b(m|magenta)\b", name): return "toner_magenta"
    if re.search(r"\b(y|yellow|amarelo)\b", name): return "toner_amarelo"
    
    return "other"

async def _get_raw_printer_data(ip: str) -> Printer | None:
    """
    Tenta conectar-se a uma impressora usando múltiplos formatos de URI.
    Retorna os dados brutos da impressora na primeira conexão bem-sucedida.
    """
    uris_to_try = [
        ip,
        f"ipp://{ip}",
        f"ipp://{ip}:631",
        f"ipp://{ip}/ipp/print",
        f"ipp://{ip}/ipp",
        f"ipps://{ip}/ipp/print"
    ]

    for uri in uris_to_try:
        try:
            async with asyncio.timeout(5):
                async with IPP(uri) as ipp:
                    return await ipp.printer()
        except Exception:
            # Continua para a próxima URI em caso de erro ou timeout
            continue
    
    # Se todas as tentativas falharem, retorna None
    return None


async def get_printer_details_ipp(ip: str) -> dict | None:
    """
    Busca os detalhes de uma impressora via IPP e formata em um dicionário
    padrão para o nosso sistema.
    """
    try:
        printer_data = await _get_raw_printer_data(ip)
        
        if not printer_data or not hasattr(printer_data, 'info'):
            return None

        # Usa getattr() para acesso seguro aos atributos, retornando um valor padrão se não existir
        details = {
            'status': 'Online',
            'status_detalhado': getattr(printer_data.info, 'state_message', 'Status não disponível'),
            'contagem_paginas': getattr(printer_data.info, 'marker_sheets_completed', -1),
            'toner_preto': -1,
            'toner_ciano': -1,
            'toner_magenta': -1,
            'toner_amarelo': -1
        }

        # Processa os níveis de toner de forma segura
        if hasattr(printer_data, 'markers') and printer_data.markers:
            for marker in printer_data.markers:
                marker_type = getattr(marker, 'marker_type', '').lower()
                
                # --- ALTERAÇÃO APLICADA AQUI: Procura por "toner" OU "ink" ---
                is_supply = any(supply in marker_type for supply in ('toner', 'ink'))

                if hasattr(marker, 'level') and marker.level >= 0 and is_supply:
                    color = _normalize_color(marker)
                    if color != "other":
                        details[color] = marker.level
        
        return details

    except Exception as e:
        print(f"Erro ao processar dados da impressora {ip} após conexão IPP: {e}")
        return None

