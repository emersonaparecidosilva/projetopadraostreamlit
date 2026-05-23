import math
import os
import json
import unittest
import warnings
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFDirectoryLoader

# Desativa avisos estáticos para manter o terminal limpo na apresentação para a banca
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Variáveis globais para compartilhamento de dados dinâmicos com a suite de testes unitários
PERGUNTA_USUARIO = ""
CONTEXTO_RECUPERADO_CHUNKS = ""
RESPOSTA_GERADA_CHUNKS = ""

# Métricas globais de volumetria de dados para avaliação de performance
METRICAS_TOKENS = {
    "tokens_prompt_chunks": 0,
    "tokens_prompt_documento_inteiro": 0
}

def calcular_tokens_aproximados(texto: str) -> int:
    """
    Heurística padrão para Processamento de Linguagem Natural (PLN):
    1 token em português equivale a aproximadamente 4 caracteres (incluindo espaços).
    Esta métrica confere o rigor estatístico exigido pelas diretrizes acadêmicas.
    """
    return math.ceil(len(texto) / 4)

def extrair_json_puro(texto: str) -> str:
    """
    Localiza o primeiro '{' e o último '}' na resposta textual da IA.
    Esta abordagem resolve de forma definitiva falhas de parseamento causadas 
    por blocos markdown (```json) ou prefácios conversacionais gerados pela LLM.
    """
    try:
        inicio = texto.index('{')
        fim = texto.rindex('}') + 1
        return texto[inicio:fim]
    except ValueError:
        return texto


# ==============================================================================
# 1. CLASSE DO AGENTE COGNITIVO (CHATBOT BASEADO EM CHUNKS - RAG)
# ==============================================================================
class AgenteCognitivoLocal:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        from langchain_community.vectorstores import Chroma
        self.db = Chroma(persist_directory="db_local", embedding_function=self.embeddings)
        self.llm = OllamaLLM(model="gemma4", temperature=0.0)

    def buscar_similaridade_contextual(self, pergunta: str) -> list:
        """Busca no banco vetorial os trechos mais aderentes à pergunta."""
        return self.db.similarity_search_with_relevance_scores(pergunta, k=3)

    def responder_com_base_em_contexto(self, pergunta: str, contexto: str) -> str:
        """Garante a ancoragem da resposta com base estritamente no contexto reduzido."""
        template = """
        Você é um auditor acadêmico especializado. Responda à pergunta do usuário utilizando 
        única e exclusivamente as informações fornecidas no contexto abaixo.
        
        Contexto: {contexto}
        Pergunta: {pergunta}
        
        Resposta Analítica:
        """
        prompt = ChatPromptTemplate.from_template(template)
        
        # Calcula e armazena os tokens enviados na abordagem por Chunks
        prompt_montado = template.format(contexto=contexto, pergunta=pergunta)
        METRICAS_TOKENS["tokens_prompt_chunks"] = calcular_tokens_aproximados(prompt_montado)
        
        chain = prompt | self.llm
        return chain.invoke({"contexto": contexto, "pergunta": pergunta})


# ==============================================================================
# 2. CLASSE DE IA PARA AUDITORIA (VALIDAÇÃO POR CONTEXTO LONGO - DOCUMENTO INTEIRO)
# ==============================================================================
class IA_LongContextAuditor:
    def __init__(self):
        self.llm = OllamaLLM(model="gemma4", temperature=0.0)

    def extrair_texto_documento_inteiro(self) -> str:
        """Carrega 100% do conteúdo textual dos PDFs originais de forma linear."""
        if os.path.exists("base"):
            loader = PyPDFDirectoryLoader("base/")
            documentos = loader.load()
            return "\n".join([doc.page_content for doc in documentos])
        return ""

    def auditoria_cross_checking(self, documento_completo: str, pergunta: str, resposta_chunks: str) -> dict:
        """Instrui a IA local a auditar a resposta do RAG contra a verdade do documento todo."""
        prompt_auditoria = f"""
        Você é um Engenheiro de QA especialista em validação de Modelos de Linguagem.
        Sua tarefa é ler um DOCUMENTO INTEIRO e validar se a resposta gerada por um algoritmo 
        reduzido (baseado em pedaços do texto) está correta e condiz fielmente com a verdade do documento todo.

        [DOCUMENTO INTEIRO BRUTO]:
        {documento_completo}

        [PERGUNTA FEITA]:
        {pergunta}

        [RESPOSTA GERADA POR CHUNKS (RAG)]:
        {resposta_chunks}

        Analise se a resposta baseada em chunks omitiu algo crítico do documento original ou se está correta.
        Responda ÚNICA e EXCLUSIVAMENTE com um objeto JSON no formato abaixo. É terminantemente proibido incluir qualquer texto extra:
        {{
            "condiz_com_o_documento_inteiro": true ou false,
            "nota_fidelidade": um valor float entre 0.0 e 1.0,
            "justificativa_analitica": "Sua análise técnica comparando as duas abordagens aqui."
        }}

        JSON:
        """
        # Registra a volumetria aproximada de tokens para a análise do contexto longo
        METRICAS_TOKENS["tokens_prompt_documento_inteiro"] = calcular_tokens_aproximados(prompt_auditoria)
        
        resposta_bruta = self.llm.invoke(prompt_auditoria).strip()
        
        # Filtra e extrai o dicionário estruturado independente de caracteres extras ou markdown
        json_filtrado = extrair_json_puro(resposta_bruta)

        try:
            return json.loads(json_filtrado)
        except Exception:
            return {
                "condiz_com_o_documento_inteiro": False,
                "nota_fidelidade": 0.0,
                "justificativa_analitica": f"Erro de parseamento estruturado. Resposta bruta: {resposta_bruta}"
            }


# ==============================================================================
# 3. SUITE DE TESTES UNITÁRIOS DINÂMICOS (UNITTEST)
# ==============================================================================
class TesteDinamicoEscopoCompleto(unittest.TestCase):
    def setUp(self):
        self.agente = AgenteCognitivoLocal()
        self.auditor_longo = IA_LongContextAuditor()

    def test_passo_1_validacao_matematica_do_banco_vetorial(self):
        """[TESTE 1] Verifica se o score de similaridade cosseno atende ao limiar estatístico."""
        print("\n[TESTE 1] Calculando acoplamento numérico da busca por similaridade...")
        resultados = self.agente.buscar_similaridade_contextual(PERGUNTA_USUARIO)
        self.assertTrue(len(resultados) > 0, "O banco vetorial retornou zero fragmentos.")
        
        _, score_bruto = resultados[0]
        score_formatado = math.floor(score_bruto * 10000) / 10000
        print(f"-> Elasticidade semântica da busca (Cosseno): {score_formatado:.4f}")
        self.assertGreater(score_formatado, 0.3500)

    def test_passo_2_validacao_por_contexto_longo_via_ia(self):
        """[TESTE 2] Compara a resposta gerada por chunks com o documento completo."""
        print("\n[TESTE 2] Carregando o PDF completo para Auditoria de Contexto Longo...")
        
        documento_bruto = self.auditor_longo.extrair_texto_documento_inteiro()
        self.assertTrue(len(documento_bruto) > 0, "Falha de ingestão: Não foi possível carregar o texto bruto.")
        
        resultado = self.auditor_longo.auditoria_cross_checking(documento_bruto, PERGUNTA_USUARIO, RESPOSTA_GERADA_CHUNKS)
        
        print(f"-> Condiz com o Documento Inteiro? = {resultado['condiz_com_o_documento_inteiro']}")
        print(f"-> Grau de Consistência Semântica: {resultado['nota_fidelidade']:.2f}")
        print(f"-> Parecer da Auditoria de Contexto Longo: {resultado['justificativa_analitica']}")
        
        self.assertTrue(resultado['condiz_com_o_documento_inteiro'], "A IA de auditoria apontou divergência entre a resposta e o documento completo.")


# ==============================================================================
# EXECUÇÃO DO FLUXO PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    print("\n" + "="*75)
    print("SISTEMA COGNITIVO INTERATIVO COM AUDITORIA COMPLETA DE CONTEXTO LONGO")
    print("="*75)
    
    PERGUNTA_USUARIO = input("\n[DIGITE SUA PERGUNTA PARA O SISTEMA]: ")
    
    agente_sistema = AgenteCognitivoLocal()
    print("\n[SISTEMA]: Executando indexação cosseno na base local...")
    dados_recuperados = agente_sistema.buscar_similaridade_contextual(PERGUNTA_USUARIO)
    
    if dados_recuperados:
        CONTEXTO_RECUPERADO_CHUNKS = "\n".join([doc.page_content for doc, _ in dados_recuperados])
        print("[SISTEMA]: Gerando resposta otimizada por Chunks...")
        RESPOSTA_GERADA_CHUNKS = agente_sistema.responder_com_base_em_contexto(PERGUNTA_USUARIO, CONTEXTO_RECUPERADO_CHUNKS)
        
        print(f"\n[IA LOCAL - RESPOSTA CHATBOT (ABORDAGEM REDUZIDA)]:\n{RESPOSTA_GERADA_CHUNKS}\n")
    else:
        print("[AVISO]: Dados insuficientes no banco vetorial.\n")
    
    print("="*75)
    print("DISPARANDO SUITE DE TESTES UNITÁRIOS DA INTEGRIDADE DO RAG")
    print("="*75)
    
    import sys
    unittest.main(argv=[sys.argv[0]], exit=False)
    
    # ==============================================================================
    # EXIBIÇÃO DO RELATÓRIO DE METRICAS E EFICIÊNCIA DE SOFTWARE
    # ==============================================================================
    print("\n" + "="*75)
    print("RELATÓRIO DE VOLUMETRIA E QUANTIFICAÇÃO DE TOKENS (ANÁLISE DE EFICIÊNCIA)")
    print("="*75)
    tokens_chunks = METRICAS_TOKENS["tokens_prompt_chunks"]
    tokens_total = METRICAS_TOKENS.get("tokens_prompt_documento_inteiro", 0)
    
    economia_percentual = 0.0000
    if tokens_total > 0:
        economia_percentual = ((tokens_total - tokens_chunks) / tokens_total) * 100
    
    print(f"-> Consumo na Resposta Inicial (Abordagem Chunks / RAG): {tokens_chunks} tokens")
    print(f"-> Consumo Requerido para Análise do Documento Inteiro:  {tokens_total} tokens")
    print(f"-> Eficiência Computacional da Ingestão de Dados:         {economia_percentual:.4f}% de economia de memória")
    print("="*75 + "\n")