import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

def executar_pipeline_automacao():
    print("==================================================")
    print("INICIANDO AUTOMAÇÃO: PIPELINE DE INGESTÃO DE DADOS")
    print("==================================================")

    # 1. Verificação de Pré-requisitos de Diretório
    if not os.path.exists("base") or not os.listdir("base"):
        print("[ERRO] A pasta 'base' está vazia ou não existe. Insira os PDFs acadêmicos nela.")
        return

    # 2. Automação de Carga: Varre e extrai o texto de todos os PDFs
    print("[PASSO 1] Lendo documentos PDF do diretório local...")
    loader = PyPDFDirectoryLoader("base/")
    documentos = loader.load()
    print(f"-> Ingestão concluída. Total de páginas processadas: {len(documentos)}")

    # 3. Fragmentação Semântica (Text Splitting)
    print("[PASSO 2] Fragmentando texto em blocos analíticos (chunks)...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=400
    )
    chunks = text_splitter.split_documents(documentos)
    print(f"-> Fragmentação concluída. Total de sub-blocos gerados: {len(chunks)}")

    # 4. Inicialização do Modelo de Embeddings Local (Ollama)
    print("[PASSO 3] Conectando ao Ollama para extração de Embeddings (nomic-embed-text)...")
    embeddings_local = OllamaEmbeddings(model="nomic-embed-text")

    # 5. Persistência Estruturada no Banco Vetorial ChromaDB
    print("[PASSO 4] Indexando e salvando vetores no banco de dados local 'db_local'...")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings_local,
        persist_directory="db_local"
    )
    print("==================================================")
    print("SUCESSO: BANCO VETORIAL GERADO NA PASTA 'db_local'")
    print("==================================================")

if __name__ == "__main__":
    executar_pipeline_automacao()