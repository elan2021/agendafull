# Midas PDV

## Descrição do Projeto
Midas PDV é uma aplicação web desenvolvida para auxiliar na gestão de agendamentos e operações de ponto de venda, especialmente voltada para salões de beleza, barbearias e negócios similares. O sistema permite o cadastro da empresa, gerenciamento de profissionais, serviços, horários de atendimento, clientes e agendamentos.

## Pré-requisitos
Para executar esta aplicação, você precisará ter instalado:
* Python (versão 3.8 ou superior recomendada)
* pip (gerenciador de pacotes Python, geralmente incluído com Python)

## Configuração do Ambiente

### 1. Clone o Repositório (Exemplo)
Se este projeto estivesse hospedado em um servidor Git, você o clonaria da seguinte forma:
```bash
git clone https://example.com/your-repo/midas_pdv.git
cd midas_pdv
```
Como você está recebendo os arquivos diretamente, pode pular esta etapa de clone e apenas certificar-se de que está no diretório raiz do projeto (`midas_pdv`).

### 2. Crie um Ambiente Virtual
É altamente recomendável usar um ambiente virtual para isolar as dependências do projeto.
```bash
python -m venv venv
```

### 3. Ative o Ambiente Virtual
* **Windows:**
  ```bash
  venv\Scripts\activate
  ```
* **macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 4. Instale as Dependências
Com o ambiente virtual ativado, instale todas as bibliotecas Python necessárias:
```bash
pip install -r requirements.txt
```

## Configuração do Banco de Dados
A aplicação utiliza SQLite como banco de dados.
* O arquivo do banco de dados, chamado `app.db`, é criado automaticamente na primeira vez que a aplicação é executada. Isso ocorre devido à chamada `db.create_all()` presente no arquivo `app.py`.
* **Localização do Banco de Dados**: `midas_pdv/instance/app.db`

## Executando a Aplicação
Após a configuração do ambiente e instalação das dependências:
1. Certifique-se de que seu ambiente virtual está ativado.
2. Navegue até o diretório raiz do projeto (`midas_pdv`), caso ainda não esteja lá.
3. Execute o seguinte comando para iniciar o servidor de desenvolvimento Flask:
   ```bash
   python app.py
   ```
4. Abra seu navegador e acesse a URL: `http://127.0.0.1:5000/`

## Estrutura do Projeto
```
midas_pdv/
├── app.py                # Arquivo principal da aplicação Flask (rotas, lógica de negócios, modelos DB)
├── instance/
│   └── app.db            # Banco de dados SQLite (criado automaticamente)
├── static/
│   ├── uploads/
│   │   └── profile_pics/ # Imagens de perfil das empresas
│   └── .gitkeep          # Placeholder para o diretório static
├── templates/            # Templates HTML renderizados pelo Flask
│   ├── add_profissionais.html
│   ├── add_servico.html
│   ├── agendamentos.html
│   ├── all_profissionais.html
│   ├── all_servicos.html
│   ├── clientes.html
│   ├── dashboard.html
│   ├── horarios.html
│   └── login.html
├── requirements.txt      # Lista de dependências Python do projeto
└── README.md             # Este arquivo
```

*   `app.py`: Arquivo principal da aplicação Flask, contendo as definições de rotas, lógica de negócios e modelos de banco de dados (SQLAlchemy).
*   `instance/`: Diretório utilizado pelo Flask para armazenar arquivos específicos da instância, como o banco de dados SQLite (`app.db`).
*   `static/`: Contém arquivos estáticos como CSS, JavaScript e imagens. As imagens de perfil carregadas pelas empresas são salvas em `static/uploads/profile_pics/`.
*   `templates/`: Armazena os templates HTML que são renderizados pela aplicação.
*   `requirements.txt`: Lista todas as dependências Python necessárias para o projeto.

## Funcionalidades Implementadas (Web UI)
*   **Autenticação**: Cadastro e Login de Empresas.
*   **Dashboard**: Painel principal acessado após o login.
*   **Profissionais**:
    *   Adicionar novos profissionais à empresa.
    *   Listar todos os profissionais cadastrados na empresa.
    *   (Funcionalidades de edição/exclusão e login de profissional não estão no escopo inicial da UI web).
*   **Serviços**:
    *   Adicionar novos serviços oferecidos pela empresa.
    *   Associar quais profissionais podem realizar cada serviço.
    *   Listar todos os serviços cadastrados.
    *   Configurar se um serviço exige sinal e qual a porcentagem.
*   **Horários**:
    *   Configurar a grade de horários de trabalho semanal para cada profissional.
    *   Definir dias de folga.
    *   Especificar horários de início e término de trabalho, e de almoço.
    *   Definir pausas entre atendimentos.
*   **Clientes**:
    *   Listar clientes cadastrados na empresa (a criação de clientes via UI web não é o foco inicial, mas é suportada via API).
*   **Agendamentos**:
    *   Listar agendamentos da empresa (a criação de agendamentos via UI web não é o foco inicial, mas é suportada via API).

## Documentação da API REST

A API RESTful do Midas PDV permite a integração com outros sistemas e a automação de tarefas. Todas as requisições à API devem incluir o cookie de sessão (`session`) após a autenticação da empresa pela interface web para serem bem-sucedidas, exceto pelos endpoints públicos (se houver).

### 1. Listar Serviços

*   **Endpoint**: `GET /api/servicos`
*   **Descrição**: Retorna uma lista de todos os serviços cadastrados para a empresa autenticada, incluindo os profissionais associados a cada serviço.
*   **Autenticação**: Requerida (sessão da empresa).
*   **Resposta em caso de Sucesso (200 OK)**:
    ```json
    [
      {
        "id": 1,
        "nome_servico": "Corte de Cabelo Masculino",
        "descricao": "Corte moderno e estilizado.",
        "duracao": 30,
        "preco": 50.00,
        "sinal": false,
        "porcentagem_sinal": null,
        "profissionais": [
          { "id": 1, "nome_profissional": "João Barbeiro" },
          { "id": 2, "nome_profissional": "Maria Cabeleireira" }
        ]
      },
      {
        "id": 2,
        "nome_servico": "Manicure Completa",
        "descricao": "Tratamento completo para mãos e unhas.",
        "duracao": 60,
        "preco": 70.00,
        "sinal": true,
        "porcentagem_sinal": 20.0,
        "profissionais": [
          { "id": 3, "nome_profissional": "Ana Manicure" }
        ]
      }
    ]
    ```
*   **Resposta em caso de Erro**:
    *   `401 Unauthorized`: Se a empresa não estiver autenticada.
      ```json
      { "error": "Unauthorized", "message": "Empresa não autenticada." }
      ```

### 2. Obter Disponibilidade de Horários

*   **Endpoint**: `GET /api/disponibilidade`
*   **Descrição**: Retorna uma lista de horários disponíveis para um profissional específico, em uma data específica, para um determinado serviço (considerando a duração do serviço).
*   **Autenticação**: Requerida.
*   **Parâmetros da Query**:
    *   `profissional_id` (obrigatório): ID do profissional.
    *   `data` (obrigatório): Data para verificar a disponibilidade (formato: `YYYY-MM-DD`).
    *   `servico_id` (obrigatório): ID do serviço (para determinar a duração).
*   **Resposta em caso de Sucesso (200 OK)**:
    ```json
    [ "09:00", "09:30", "10:00", "14:00", "14:30" ]
    ```
    (Retorna uma lista vazia `[]` se não houver horários disponíveis, se o profissional não trabalhar no dia, ou se for dia de folga.)
*   **Respostas em caso de Erro**:
    *   `400 Bad Request`: Parâmetros faltando ou em formato inválido.
      ```json
      { "error": "Missing required parameters", "message": "profissional_id, data (YYYY-MM-DD), e servico_id são obrigatórios." }
      ```
      ```json
      { "error": "Invalid parameter format", "message": "ID do profissional/serviço deve ser inteiro, data deve ser YYYY-MM-DD." }
      ```
    *   `401 Unauthorized`: Empresa não autenticada.
    *   `404 Not Found`: Profissional ou Serviço não encontrado ou não pertence à empresa.
      ```json
      { "error": "Not found", "message": "Profissional não encontrado ou não pertence à empresa." }
      ```

### 3. Cadastrar Novo Cliente

*   **Endpoint**: `POST /api/clientes`
*   **Descrição**: Cadastra um novo cliente para a empresa autenticada.
*   **Autenticação**: Requerida.
*   **Corpo da Requisição (JSON)**:
    ```json
    {
      "nome_cliente": "Carlos Silva",
      "telefone": "11987654321"
    }
    ```
*   **Resposta em caso de Sucesso (201 Created)**:
    ```json
    {
      "id": 1,
      "empresa_id": 123,
      "nome_cliente": "Carlos Silva",
      "telefone": "11987654321",
      "valor_gasto": 0.0
    }
    ```
*   **Respostas em caso de Erro**:
    *   `400 Bad Request`: Dados faltando no corpo da requisição.
      ```json
      { "error": "Missing data", "message": "nome_cliente e telefone são obrigatórios." }
      ```
    *   `401 Unauthorized`: Empresa não autenticada.
    *   `409 Conflict`: Cliente com este telefone já cadastrado para esta empresa.
      ```json
      { "error": "Conflict", "message": "Cliente com este telefone já cadastrado para esta empresa." }
      ```
    *   `500 Internal Server Error`: Erro ao salvar no banco.

### 4. Buscar Cliente por Telefone

*   **Endpoint**: `GET /api/clientes/buscar`
*   **Descrição**: Busca um cliente cadastrado para a empresa autenticada pelo número de telefone.
*   **Autenticação**: Requerida.
*   **Parâmetros da Query**:
    *   `telefone` (obrigatório): Número de telefone do cliente.
*   **Resposta em caso de Sucesso (200 OK)**:
    ```json
    {
      "id": 1,
      "empresa_id": 123,
      "nome_cliente": "Carlos Silva",
      "telefone": "11987654321",
      "valor_gasto": 0.0
    }
    ```
*   **Respostas em caso de Erro**:
    *   `400 Bad Request`: Parâmetro `telefone` faltando.
      ```json
      { "error": "Missing query parameter", "message": "Parâmetro \"telefone\" é obrigatório." }
      ```
    *   `401 Unauthorized`: Empresa não autenticada.
    *   `404 Not Found`: Cliente não encontrado.
      ```json
      { "message": "Cliente não encontrado." }
      ```

### 5. Criar Novo Agendamento

*   **Endpoint**: `POST /api/agendamentos`
*   **Descrição**: Cria um novo agendamento para a empresa autenticada.
*   **Autenticação**: Requerida.
*   **Corpo da Requisição (JSON)**:
    ```json
    {
      "servico_id": 1,
      "cliente_id": 1,
      "profissional_id": 1,
      "data_agendamento": "YYYY-MM-DD",
      "horario_inicio": "HH:MM"
    }
    ```
*   **Resposta em caso de Sucesso (201 Created)**:
    ```json
    {
      "id": 1,
      "servico_id": 1,
      "cliente_id": 1,
      "profissional_id": 1,
      "data_agendamento": "YYYY-MM-DD",
      "horario_inicio": "HH:MM",
      "horario_fim": "HH:MM",
      "valor_total": 50.00,
      "status": "Confirmado"
    }
    ```
*   **Respostas em caso de Erro**:
    *   `400 Bad Request`: Dados faltando ou em formato inválido.
    *   `401 Unauthorized`: Empresa não autenticada.
    *   `404 Not Found`: Serviço, Cliente ou Profissional não encontrado ou não pertence à empresa.
    *   `409 Conflict`: Horário indisponível ou conflitante.
      ```json
      { "error": "Unavailable", "message": "Horário já reservado ou conflitante." }
      ```
    *   `500 Internal Server Error`: Erro ao salvar no banco.

### 6. Atualizar Status do Agendamento

*   **Endpoint**: `PUT /api/agendamentos/<int:agendamento_id>/status`
*   **Descrição**: Atualiza o status de um agendamento existente.
*   **Autenticação**: Requerida.
*   **Parâmetro da URL**:
    *   `agendamento_id`: ID do agendamento a ser atualizado.
*   **Corpo da Requisição (JSON)**:
    ```json
    {
      "status": "Concluído"
    }
    ```
    (Status permitidos: 'Pendente', 'Confirmado', 'Cancelado', 'Concluído', 'Não Compareceu')
*   **Resposta em caso de Sucesso (200 OK)**:
    ```json
    {
      "id": 1,
      "status": "Concluído",
      "message": "Status do agendamento atualizado com sucesso."
    }
    ```
*   **Respostas em caso de Erro**:
    *   `400 Bad Request`: Campo `status` faltando ou valor inválido.
    *   `401 Unauthorized`: Empresa não autenticada.
    *   `404 Not Found`: Agendamento não encontrado ou não pertence à empresa.
    *   `500 Internal Server Error`: Erro ao salvar no banco.

### 7. Listar Agendamentos por Data

*   **Endpoint**: `GET /api/agendamentos/data`
*   **Descrição**: Retorna uma lista de todos os agendamentos para a empresa autenticada em uma data específica.
*   **Autenticação**: Requerida.
*   **Parâmetros da Query**:
    *   `data` (obrigatório): Data para buscar os agendamentos (formato: `YYYY-MM-DD`).
*   **Resposta em caso de Sucesso (200 OK)**:
    ```json
    [
      {
        "id": 1,
        "servico": { "id": 1, "nome_servico": "Corte de Cabelo" },
        "cliente": { "id": 1, "nome_cliente": "Carlos Silva", "telefone": "11987654321" },
        "profissional": { "id": 1, "nome_profissional": "João Barbeiro" },
        "data_agendamento": "YYYY-MM-DD",
        "horario_inicio": "10:00",
        "horario_fim": "10:30",
        "valor_total": 50.00,
        "status": "Confirmado"
      }
      // ... outros agendamentos
    ]
    ```
*   **Respostas em caso de Erro**:
    *   `400 Bad Request`: Parâmetro `data` faltando ou em formato inválido.
    *   `401 Unauthorized`: Empresa não autenticada.

(Esta seção pode ser expandida com detalhes de cada endpoint se necessário).
