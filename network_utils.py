# --------------------------------------------------------------------------------
# network_utils.py (Módulo de Utilitários de Rede)
#
# Autor: Emerson A. Silva
# Data: 20/10/2025
#
# Descrição:
# Versão final utilizando a abordagem híbrida: PING para conectividade e
# IPP (via pyipp) para buscar detalhes das impressoras online.
# --------------------------------------------------------------------------------

import streamlit as st
import concurrent.futures
import database as db
import ipp_utils as ipp  # <-- Importa o novo módulo IPP
import asyncio
from datetime import datetime
import platform
import subprocess

def ping_host(host):
    """Executa um único ping em um host para verificar a conectividade."""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-w', '2', host]
    
    try:
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False

def check_printer_details(printer):
    """
    Verifica os detalhes de uma impressora: ping para conectividade, IPP para detalhes.
    """
    printer_id = printer['id']
    ip_address = printer.get('endereco_ip')
    
    result_data = {
        'id': printer_id, 'status': 'Offline', 'status_detalhado': 'Não responde (Ping)',
        'toner_preto': printer.get('toner_preto', -1), 'toner_ciano': printer.get('toner_ciano', -1),
        'toner_magenta': printer.get('toner_magenta', -1), 'toner_amarelo': printer.get('toner_amarelo', -1),
        'contagem_paginas': printer.get('contagem_paginas', -1), 'ultima_verificacao': datetime.now()
    }
    
    if not ip_address or not ping_host(ip_address):
        return result_data

    # --- A MÁGICA ACONTECE AQUI ---
    # Se o ping funcionou, executamos a função assíncrona do ipp_utils
    # dentro de um event loop criado pelo asyncio.run()
    ipp_details = asyncio.run(ipp.get_printer_details_ipp(ip_address))
    
    if ipp_details:
        result_data.update(ipp_details)
    else:
        # Se o ping funcionou mas o IPP não, a impressora está online mas não gerenciável
        result_data['status'] = 'Online'
        result_data['status_detalhado'] = 'Online (Não responde ao protocolo IPP)'

    return result_data

def update_all_printers_status(conn, printers_df, show_spinner=True):
    """Orquestra a verificação de todas as impressoras em paralelo."""
    online_count = 0
    total_count = len(printers_df)
    
    if total_count == 0:
        return 0, 0
        
    all_results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_printer = {executor.submit(check_printer_details, printer): printer for index, printer in printers_df.iterrows()}
        
        progress_bar = None
        if show_spinner:
            try:
                progress_bar = st.progress(0, text="Iniciando verificação...")
            except st.errors.StreamlitAPIException:
                progress_bar = None

        for i, future in enumerate(concurrent.futures.as_completed(future_to_printer)):
            try:
                result = future.result()
                all_results.append(result)
            except Exception as exc:
                printer_info = future_to_printer[future]
                print(f"Erro ao processar a impressora {printer_info.get('nome')}: {exc}")
            
            if show_spinner and progress_bar:
                progress_text = f"Verificando {i+1} de {total_count} impressoras..."
                progress_bar.progress((i + 1) / total_count, text=progress_text)

    for printer_data in all_results:
        db.update_printer_details(conn, printer_data)
        if printer_data.get('status') == 'Online':
            online_count += 1
            
    return online_count, total_count

