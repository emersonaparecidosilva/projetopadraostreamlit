# 📘 Guia de Instalação e Execução do Aplicativo

Olá! Este é um guia completo para você configurar e rodar o aplicativo padrão em streamlit com controle de usuários em seu computador.  
Siga os passos com atenção e tudo dará certo! 🚀

---

## 📖 O que este guia vai te ensinar?

1. **Instalar o MySQL:** O banco de dados onde todas as informações ficarão salvas.  
2. **Preparar o Projeto:** Baixar os arquivos do projeto e instalar as ferramentas necessárias.  
3. **Configurar a Conexão:** Fazer o aplicativo "conversar" com o banco de dados.  
4. **Rodar o Aplicativo:** Colocar o sistema para funcionar.

---

## 🧩 Passo 1: Instalar o MySQL (Nosso Banco de Dados)

O **MySQL Server** é o programa que vai armazenar os dados dos usuários.

### 🔽 Baixe o Instalador

- Acesse o site oficial: [MySQL Community Downloads](https://dev.mysql.com/downloads/)
- Procure pela versão **Windows x86, 64-bit MSI Installer** e clique em **Download**.
- Na página seguinte, clique em **“No thanks, just start my download.”**

### ⚙️ Instale o MySQL

1. Execute o arquivo que você baixou.  
2. Na tela **“Choosing a Setup Type”**, selecione **Developer Default** e clique em **Next**.  
3. Se o instalador pedir pré-requisitos, apenas clique em **Execute** e depois **Next**.  
4. Continue clicando em **Next** até chegar na tela **Accounts and Roles**.  
5. ⚠️ **MUITO IMPORTANTE:** Crie a senha para o usuário `root` e **anote-a em um lugar seguro!**  
6. Após definir a senha, continue clicando em **Next → Execute → Finish** para concluir.

---

## 🐍 Passo 2: Preparar o Ambiente Python e o Projeto

Agora vamos preparar o ambiente para rodar o código do nosso aplicativo.

### 💾 Instale o Python 3.13

1. Acesse [python.org](https://www.python.org/downloads/) e baixe a versão **3.13**.  
2. Durante a instalação, **marque a caixa** `Add Python to PATH` antes de clicar em **Install Now**.

### 🧭 Abra o Terminal

Pressione a tecla **Windows**, digite **cmd** e pressione **Enter**.

---

### 📂 Obtenha os Arquivos do Projeto

```bash
cd PastadoProjeto
git clone https://github.com/emersonaparecidosilva/projetopadraostreamlit.git

### Instale as bibliotecas 

pip install streamlit pandas mysql-connector-python bcrypt streamlit-option-menu

### 🐍 Passo 3: Configurar o Arquivo de Segredos (secrets.toml)
- Crie a Pasta .streamlit
    - Dentro da pasta do projeto, crie uma nova pasta e renomeie-a para exatamente .streamlit (com o ponto no início).

- Crie o Arquivo secrets.toml
    -  Abra o Bloco de Notas, cole o conteúdo abaixo e salve o arquivo como secrets.toml dentro da pasta .streamlit.
    [mysql]
    host = "localhost"
    user = "USUARIO"
    password = "SUA_SENHA_AQUI"
- Rode o app pelo terminal = streamlit run app.py

### Para entrar no sistema pela primeira vez, use as credenciais de administrador padrão:

- Email: admin@projeto.com
- Senha: Projeto2025
