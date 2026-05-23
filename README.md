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

O **MySQL Server** é o programa que vai armazenar os dados de nossa aplicação.

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

### 🧭 Abra o Terminal de sua preferência e Obtenha os Arquivos do Projeto

```bash
cd PastadoProjeto
git clone https://github.com/emersonaparecidosilva/projetopadraostreamlit.git

### Habilite o ambiente Virtual
python -m venv .venv

### Ative o ambiente
.venv\Scripts\activate

### Caso os scripts estejam bloqueados:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

### Instale as bibliotecas 
pip install -r requirements.txt
````

### 🐍 Passo 3: Configurar o Arquivo de Segredos (secrets.toml)
- Crie a Pasta .streamlit
    - Dentro da pasta do projeto, crie uma nova pasta e renomeie-a para exatamente .streamlit (com o ponto no início).

-  Crie e edite o arquivo secrets.toml, cole o conteúdo abaixo e salve o arquivo dentro da pasta .streamlit.
    [mysql]
    host = "localhost"
    user = "USUARIO"
    password = "SUA_SENHA_AQUI"
    database = "pio"

    - Configuração do seu E-mail (Ex: Gmail)
    [email]
    sender_email = "SEU EMAIL@gmail.com"
    sender_password = "Sua Senha de APP 12 DIGITOS"
    
### 🐍 Passo 4: Rode o app pelo terminal na pasta do projeto = streamlit run app.py

- Para entrar no sistema pela primeira vez, observe o retorno no terminal:

    You can now view your Streamlit app in your browser.
    
      Local URL: http://localhost:8501
      
      Network URL: http://SEU IP:8501
  
- PRIMEIRA EXECUÇÃO: UTILIZADOR ADMIN CRIADO
  
    Email: admin@projeto.com
  
    Senha Temporária: Senha exposta no terminal
  
    Por favor, guarde esta senha e altere-a no primeiro login.

  ### 🐍 Passo 5: Utilize o sistema, navegue e configure como quiser.
