import os
import io
import unittest
from contextlib import redirect_stdout
import streamlit as st

# Importa os módulos locais de automação e testes do seu projeto
import automacao_banco
import agente_testes

def show_home_page(conn):
    st.title("🏠 Dashboard Automático - RAG")
    st.write("Bem-vindo! Utilize as ferramentas abaixo para ingerir dados e interagir com o agente cognitivo.")

    # Variável de controle de sessão para resetar os campos quando o botão Limpar for acionado
    if "clear_key" not in st.session_state:
        st.session_state.clear_key = 0

    # ==========================================
    # 1. UPLOAD E AUTOMAÇÃO (automacao_banco.py)
    # ==========================================
    st.header("1. Ingestão de Documentos (PDF)")
    
    # Campo para upload do arquivo PDF
    uploaded_file = st.file_uploader(
        "Faça o upload do seu arquivo PDF acadêmico", 
        type=["pdf"], 
        key=f"uploader_{st.session_state.clear_key}"
    )
    
    if uploaded_file is not None:
        # Garante que o diretório base exista
        base_dir = "base"
        os.makedirs(base_dir, exist_ok=True)
        
        # Salva o arquivo fisicamente na pasta base/
        file_path = os.path.join(base_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.success(f"Arquivo '{uploaded_file.name}' salvo na pasta 'base' com sucesso!")
        
        # Botão para executar a automação
        if st.button("Executar Pipeline de Automação (Ler e Indexar)"):
            with st.spinner("Lendo e indexando os documentos. Isso pode demorar um pouco..."):
                # Redireciona os "prints" do console para o Streamlit
                f_out = io.StringIO()
                with redirect_stdout(f_out):
                    automacao_banco.executar_pipeline_automacao()
                st.text(f_out.getvalue())
                st.success("Pipeline executado com sucesso!")

    st.divider()

    # ==========================================
    # 2. INTERAÇÃO E TESTES (agente_testes.py)
    # ==========================================
    st.header("2. Interação com Agente Cognitivo e Testes")
    
    # Campo de pergunta
    pergunta = st.text_input("Digite sua pergunta para o sistema:", key=f"pergunta_{st.session_state.clear_key}")
    
    if st.button("Enviar Pergunta"):
        if not pergunta:
            st.warning("Por favor, digite uma pergunta.")
        else:
            with st.spinner("Buscando similaridades e gerando resposta..."):
                # Instancia o agente cognitivo
                agente_sistema = agente_testes.AgenteCognitivoLocal()
                
                # Executa a busca no banco vetorial
                dados_recuperados = agente_sistema.buscar_similaridade_contextual(pergunta)
                
                if dados_recuperados:
                    # Gera a resposta com os chunks recuperados
                    contexto = "\n".join([doc.page_content for doc, _ in dados_recuperados])
                    resposta = agente_sistema.responder_com_base_em_contexto(pergunta, contexto)
                    
                    st.subheader("🤖 IA Local - Resposta Chatbot (Abordagem Reduzida):")
                    st.info(resposta)
                    
                    # Como agente_testes utiliza variáveis globais na suite unitária, nós as atualizamos aqui
                    agente_testes.PERGUNTA_USUARIO = pergunta
                    agente_testes.CONTEXTO_RECUPERADO_CHUNKS = contexto
                    agente_testes.RESPOSTA_GERADA_CHUNKS = resposta
                    
                    st.subheader("🧪 Suite de Testes Unitários e Integridade RAG")
                    
                    f_testes = io.StringIO()
                    with redirect_stdout(f_testes):
                        # Carrega e roda apenas os testes unitários do escopo completo dinamicamente
                        suite = unittest.TestLoader().loadTestsFromTestCase(agente_testes.TesteDinamicoEscopoCompleto)
                        runner = unittest.TextTestRunner(stream=f_testes, verbosity=2)
                        runner.run(suite)
                        
                        # Extrai e imprime o relatório de métricas no final
                        print("\n" + "="*75)
                        print("RELATÓRIO DE VOLUMETRIA E QUANTIFICAÇÃO DE TOKENS (ANÁLISE DE EFICIÊNCIA)")
                        print("="*75)
                        tokens_chunks = agente_testes.METRICAS_TOKENS["tokens_prompt_chunks"]
                        tokens_total = agente_testes.METRICAS_TOKENS.get("tokens_prompt_documento_inteiro", 0)
                        
                        economia_percentual = 0.0000
                        if tokens_total > 0:
                            economia_percentual = ((tokens_total - tokens_chunks) / tokens_total) * 100
                        
                        print(f"-> Consumo na Resposta Inicial (Abordagem Chunks / RAG): {tokens_chunks} tokens")
                        print(f"-> Consumo Requerido para Análise do Documento Inteiro:  {tokens_total} tokens")
                        print(f"-> Eficiência Computacional da Ingestão de Dados:         {economia_percentual:.4f}% de economia de memória")
                        print("="*75 + "\n")
                    
                    # Exibe toda a saída do terminal (testes e métricas) capturada pelo stdout
                    st.text(f_testes.getvalue())
                else:
                    st.warning("Dados insuficientes no banco vetorial. Tente ingerir documentos primeiro.")

    st.divider()

    # ==========================================
    # 3. LIMPEZA DE TELA
    # ==========================================
    if st.button("🧹 Limpar Tela", use_container_width=True):
        # Atualiza a chave iterativa, o que esvaziará e resetará todos os inputs atrelados a ela.
        st.session_state.clear_key += 1
        st.rerun()
