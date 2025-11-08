# Documento de Projeto de Software: Moneytora

## 1. Introdução

Este documento detalha o projeto de desenvolvimento do software **Moneytora**, um sistema multiagente de finanças pessoais concebido no contexto do evento AKCIT Camp. O objetivo principal do Moneytora é automatizar e simplificar a gestão financeira dos usuários, empregando uma arquitetura inovadora baseada em múltiplos agentes de Inteligência Artificial (IA) que trabalham de forma coordenada. A proposta central é transformar dados não estruturados de transações financeiras, como os recebidos por e-mail ou notificações, em informações organizadas e acionáveis, oferecendo aos usuários uma visão clara de seus hábitos de consumo e um assistente virtual para orientação financeira.

O sistema se propõe a extrair, classificar e analisar dados de transações de forma automática, culminando em uma interface interativa onde o usuário pode visualizar seus gastos em dashboards e conversar com um "Agente Coach" para obter insights sobre suas finanças. O projeto prioriza a orquestração inteligente entre os agentes, focando na inovação da arquitetura de IA como diferencial competitivo.

## 2. Convenções, Termos e Abreviações

| Termo/Abreviação | Descrição |
| :--- | :--- |
| **IA** | Inteligência Artificial. |
| **Agente** | Componente de software autônomo, especializado em uma tarefa específica. |
| **Agente Extrator** | Agente responsável por extrair dados estruturados de um texto não estruturado. |
| **Agente Classificador** | Agente que categoriza uma transação com base no nome da empresa. |
| **Agente de Segurança** | Agente que monitora e filtra as interações do usuário para prevenir ataques. |
| **Agente Coach** | Agente final que interage com o usuário, fornecendo insights financeiros. |
| **MVP** | Produto Mínimo Viável (Minimum Viable Product). Versão inicial do produto com funcionalidades essenciais. |
| **Tool Use / Tool Calling** | Capacidade de um agente de IA utilizar ferramentas externas (APIs, bancos de dados) para completar tarefas. |
| **Guardrail** | Mecanismo de segurança para garantir que o comportamento de um sistema de IA permaneça dentro de limites seguros. |
| **Prompt Injection** | Tipo de ataque em que um usuário insere instruções maliciosas em um prompt para manipular a saída de um modelo de IA. |
| **JSON** | JavaScript Object Notation. Formato leve de troca de dados. |
| **UI** | Interface do Usuário (User Interface). |
| **API** | Interface de Programação de Aplicações (Application Programming Interface). |
| **DER** | Diagrama de Entidade-Relacionamento. Modelo conceitual de dados. |
| **MER** | Modelo de Entidade-Relacionamento. Representação mais detalhada que o DER. |

## 3. Identificação dos Envolvidos no Projeto

O desenvolvimento do projeto será dividido entre uma equipe de quatro desenvolvedores, cada um com um foco de atuação específico, conforme detalhado na proposta inicial.

| Papel | Foco de Atuação |
| :--- | :--- |
| **Dev 1** | Arquiteto / Orquestrador |
| **Dev 2** | Agente Extrator & Agente de Segurança |
| **Dev 3** | Agente Classificador & Tool Call |
| **Dev 4** | UI / Coach |

## 4. Problema de Negócio

A gestão de finanças pessoais é um desafio para muitos indivíduos, que frequentemente lidam com um grande volume de transações dispersas em diferentes formatos (e-mails de confirmação de PIX, notificações de compras no cartão, etc.). O processo manual de coletar, organizar e categorizar esses gastos é tedioso, propenso a erros e raramente realizado de forma consistente. Como resultado, as pessoas perdem a visibilidade sobre seus hábitos de consumo, dificultando o planejamento financeiro, a identificação de oportunidades de economia e o controle do orçamento.

O Moneytora endereça este problema ao propor uma solução que automatiza todo o fluxo, desde a captura da informação até a geração de insights. A ausência de uma ferramenta que integre de forma inteligente a extração de dados, a classificação automática e a interação por meio de uma interface conversacional representa uma oportunidade de mercado para uma solução inovadora e de alto valor agregado.

## 5. Escopo e Não Escopo

### Escopo do MVP

O foco do MVP é validar a arquitetura de orquestração de agentes e a funcionalidade central do sistema. Estão incluídas no escopo as seguintes funcionalidades:

- **Entrada de Dados Manual**: O usuário irá copiar e colar o texto de uma notificação de transação em uma interface web.
- **Processamento por Agentes**: O sistema irá processar o texto através do Agente Extrator e do Agente Classificador.
- **Armazenamento de Transações**: As informações estruturadas e classificadas serão armazenadas em um banco de dados.
- **Visualização de Dados**: A interface web exibirá dashboards e gráficos básicos, atualizados em tempo real, com base nas transações processadas.
- **Interação com Coach**: O usuário poderá interagir com o Agente Coach por meio de um chat para fazer perguntas sobre seus gastos.
- **Segurança Básica**: Implementação de um Agente de Segurança para mitigar riscos de prompt injection.

### Fora do Escopo do MVP

Para garantir o foco e a viabilidade do projeto no prazo estipulado, as seguintes funcionalidades não serão incluídas no MVP:

- **Integração Automática com E-mail**: A conexão direta com serviços de e-mail (Gmail, Outlook) via OAuth ou IMAP para leitura automática de transações não será implementada.
- **Múltiplos Usuários**: O sistema será projetado para um único usuário, sem sistema de contas ou autenticação.
- **Aplicativo Móvel**: Não haverá desenvolvimento de um aplicativo nativo para dispositivos móveis.
- **Notificações Push**: O sistema não enviará notificações ativas para o usuário.
- **Conexão com Contas Bancárias**: A integração direta com contas bancárias via Open Banking ou APIs de instituições financeiras está fora de escopo.

## 6. Entrevistas/Reuniões Realizadas

Até o presente momento, não foram realizadas entrevistas ou reuniões formais com usuários finais. Toda a concepção do projeto e a definição de requisitos foram baseadas exclusivamente no documento de proposta "Proposta de Projeto: Moneytora (AKCIT Camp)", que serve como a principal fonte de informação para a elaboração deste documento.

## 7. Requisitos do Usuário

Os requisitos a seguir descrevem as necessidades e expectativas do usuário final em relação ao sistema Moneytora.

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| RU-01 | Registrar uma transação | Como usuário, eu quero poder inserir facilmente os detalhes de uma transação financeira no sistema, colando o texto de uma notificação que recebi. |
| RU-02 | Ver minhas despesas categorizadas | Como usuário, eu quero que o sistema categorize automaticamente minhas despesas (ex: alimentação, transporte) para que eu possa entender para onde meu dinheiro está indo. |
| RU-03 | Visualizar um resumo dos meus gastos | Como usuário, eu quero ter acesso a gráficos e dashboards que mostrem um resumo visual das minhas finanças, como o total de gastos por categoria ou a evolução das despesas ao longo do tempo. |
| RU-04 | Conversar sobre minhas finanças | Como usuário, eu quero poder fazer perguntas em linguagem natural sobre meus gastos (ex: "Quanto gastei com restaurantes este mês?") e receber respostas claras e diretas. |
| RU-05 | Ter segurança ao usar o sistema | Como usuário, eu quero ter a garantia de que minhas interações com o sistema são seguras e que não há risco de manipulação ou comportamento inesperado da IA. |

## 8. Tipos de Usuários/Papéis

Para a versão MVP do sistema Moneytora, será considerado apenas um tipo de usuário, que engloba todas as interações com a plataforma.

| Papel | Descrição |
| :--- | :--- |
| **Usuário Final** | Indivíduo que utiliza o sistema para gerenciar suas finanças pessoais. Este usuário insere os dados das transações, visualiza os dashboards e interage com o Agente Coach para obter insights. |

## 9. Requisitos de Sistema

Os requisitos de sistema (também conhecidos como requisitos funcionais e não funcionais) descrevem o que o sistema deve fazer para atender aos requisitos do usuário.

### Requisitos Funcionais

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| RF-01 | Extração de Dados de Transação | O sistema deve ser capaz de receber uma string de texto e extrair dela as seguintes informações: valor da transação, nome da empresa/estabelecimento e data da transação. |
| RF-02 | Estruturação dos Dados | As informações extraídas devem ser formatadas em um objeto JSON padronizado. |
| RF-03 | Classificação de Transação | O sistema deve classificar a transação em uma categoria predefinida (ex: Alimentação, Transporte, Lazer) com base no nome da empresa. |
| RF-04 | Persistência de Dados | O sistema deve armazenar os dados estruturados e classificados de cada transação em um banco de dados. |
| RF-05 | Geração de Gráficos | O sistema deve gerar e exibir gráficos (ex: gráfico de pizza de gastos por categoria) com base nos dados armazenados. |
| RF-06 | Atualização de Dashboard | A interface do usuário deve exibir os gráficos e dados de forma atualizada, refletindo as transações inseridas. |
| RF-07 | Processamento de Linguagem Natural | O sistema deve ser capaz de interpretar perguntas do usuário feitas em linguagem natural sobre seus dados financeiros. |
| RF-08 | Acesso a Dados para Resposta | O Agente Coach deve acessar o banco de dados de transações para formular respostas às perguntas do usuário. |
| RF-09 | Filtragem de Prompt | O sistema deve analisar o prompt do usuário antes de processá-lo pelo Agente Coach para identificar e bloquear possíveis tentativas de prompt injection. |

### Requisitos Não Funcionais

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| RNF-01 | Desempenho | O processamento de uma transação, desde a inserção do texto até a atualização do dashboard, deve ser concluído em menos de 5 segundos. |
| RNF-02 | Usabilidade | A interface do usuário deve ser simples e intuitiva, permitindo que um novo usuário consiga operar o sistema sem a necessidade de um tutorial. |
| RNF-03 | Segurança | O sistema deve implementar uma camada de segurança (Guardrail) para prevenir que entradas maliciosas causem comportamentos indesejados ou exponham dados sensíveis. |
| RNF-04 | Tecnologia | A solução deve ser desenvolvida utilizando Python, com uma arquitetura de agentes (preferencialmente com LangGraph) e uma interface web criada com Streamlit ou Gradio. |
| RNF-05 | Mock de Ferramenta | Para o MVP, a ferramenta de classificação de categorias pode ser um mock (dicionário em Python) para garantir a prova de conceito do "tool call". |

## 10. Regras de Negócio

As regras de negócio definem as políticas, condições e restrições que governam o funcionamento do sistema.

| ID | Regra de Negócio | Descrição |
| :--- | :--- | :--- |
| RN-01 | Formato de Extração de Dados | Toda transação processada pelo Agente Extrator deve obrigatoriamente conter: `valor` (numérico), `empresa` (string) e `data` (string no formato AAAA-MM-DD). |
| RN-02 | Classificação Obrigatória | Nenhuma transação pode ser armazenada no sistema sem uma categoria associada. Se o Agente Classificador não conseguir determinar a categoria, uma categoria padrão "Outros" deve ser atribuída. |
| RN-03 | Moeda Padrão | Todos os valores monetários devem ser considerados e armazenados em Real (BRL), não sendo necessário suporte para múltiplas moedas no MVP. |
| RN-04 | Bloqueio de Prompts Maliciosos | Se o Agente de Segurança identificar um prompt como uma ameaça potencial (ex: tentativa de ignorar instruções, revelar informações do sistema), a interação deve ser bloqueada e uma mensagem padrão de recusa deve ser exibida ao usuário. |
| RN-05 | Unicidade de Transação | O sistema não implementará uma verificação de duplicidade de transações no MVP. A responsabilidade por não inserir dados duplicados é do usuário. |
| RN-06 | Acesso aos Dados pelo Coach | O Agente Coach só pode acessar e processar os dados de transações que já foram extraídos e classificados. Ele não tem acesso direto ao texto original inserido pelo usuário. |

## 11. Dependência/Relação entre Requisitos e Regras de negócio

| Requisito(s) | Regra(s) de Negócio Associada(s) | Justificativa |
| :--- | :--- | :--- |
| RF-01, RF-02 | RN-01 | A RN-01 define o contrato de dados que os requisitos de extração e estruturação devem seguir para garantir a consistência do sistema. |
| RF-03, RF-04 | RN-02 | A RN-02 impõe a obrigatoriedade da classificação antes do armazenamento, garantindo a integridade dos dados para análise futura. |
| RF-01 | RN-03 | A RN-03 simplifica o requisito de extração ao definir uma única moeda, evitando a complexidade de conversão e formatação de múltiplos padrões monetários. |
| RF-09 | RN-04 | A RN-04 detalha o comportamento esperado do sistema quando o requisito de filtragem de prompt identifica uma ameaça, especificando a ação de bloqueio. |
| RF-08 | RN-06 | A RN-06 estabelece uma fronteira de segurança e responsabilidade, garantindo que o Agente Coach opere apenas sobre dados curados e estruturados, em linha com o requisito de acesso. |

## 12. Diagramas de Casos de Uso

O diagrama de casos de uso apresenta uma visão geral das interações entre o usuário final e o sistema Moneytora, identificando as principais funcionalidades oferecidas.

![Diagrama de Casos de Uso](diagrama_casos_uso.png)

## 13. Documentação dos Atores

| Ator | Descrição |
| :--- | :--- |
| **Usuário Final** | Pessoa física que utiliza o sistema Moneytora para gerenciar suas finanças pessoais. Este ator interage com o sistema inserindo dados de transações, visualizando dashboards e consultando o coach financeiro para obter insights e recomendações. |

## 14. Documentação dos Casos de Uso

### UC-01: Inserir Transação

**Descrição**: O usuário insere uma nova transação financeira no sistema, colando o texto de uma notificação recebida (ex: e-mail de PIX, notificação de compra).

**Ator Principal**: Usuário Final

**Pré-condições**: O usuário possui acesso à interface web do sistema.

**Fluxo Principal**:
1. O usuário acessa a interface web do sistema.
2. O usuário cola o texto da transação no campo apropriado.
3. O usuário aciona a função de processamento.
4. O sistema invoca o caso de uso UC-04 (Extrair Dados da Transação).
5. O sistema invoca o caso de uso UC-05 (Classificar Transação).
6. O sistema invoca o caso de uso UC-06 (Armazenar Transação).
7. O sistema exibe uma mensagem de confirmação ao usuário.

**Pós-condições**: A transação é armazenada no banco de dados e está disponível para visualização e consulta.

**Fluxos Alternativos**:
- **FA-01**: Se o texto inserido não contiver informações suficientes para extração, o sistema exibe uma mensagem de erro e solicita que o usuário revise a entrada.

---

### UC-02: Visualizar Dashboard

**Descrição**: O usuário visualiza gráficos e resumos de suas finanças na interface web.

**Ator Principal**: Usuário Final

**Pré-condições**: Pelo menos uma transação foi inserida e armazenada no sistema.

**Fluxo Principal**:
1. O usuário acessa a interface web do sistema.
2. O sistema recupera os dados de transações do banco de dados.
3. O sistema gera gráficos (ex: gráfico de pizza por categoria, gráfico de linha de evolução temporal).
4. O sistema exibe os gráficos na interface.

**Pós-condições**: O usuário visualiza os dados financeiros de forma gráfica.

**Fluxos Alternativos**:
- **FA-01**: Se não houver transações armazenadas, o sistema exibe uma mensagem informando que não há dados para exibir.

## 15. Guia de Execução e Testes

Para executar a API em ambiente local siga as etapas abaixo:

1. **Configurar o ambiente virtual (opcional, porém recomendado)**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows PowerShell
   ```

2. **Instalar as dependências**

   ```bash
   pip install -r requirements.txt
   ```

3. **Inicializar o banco de dados**

   A aplicação utiliza um banco SQLite (`moneytora.db`). Após alterações no modelo de dados, delete o arquivo antigo (se existir) para permitir a recriação das tabelas:

   ```bash
   rm -f moneytora.db
   ```

   O banco será recriado automaticamente ao iniciar a aplicação ou executar os testes.

4. **Configurar variáveis de ambiente opcionais**

   - `GOOGLE_API_KEY`: chave da API Gemini utilizada pelo agente extrator.

5. **Executar o servidor FastAPI**

   ```bash
   uvicorn app.main:app --reload
   ```

6. **Executar a suíte de testes automatizados**

   ```bash
   pytest
   ```

Os testes utilizam o `TestClient` do FastAPI e inicializam uma base limpa para cada caso de teste, garantindo isolamento entre os cenários.

---

### UC-03: Consultar Coach Financeiro

**Descrição**: O usuário faz uma pergunta em linguagem natural ao Agente Coach e recebe uma resposta baseada em seus dados financeiros.

**Ator Principal**: Usuário Final

**Pré-condições**: O usuário possui acesso à interface web do sistema.

**Fluxo Principal**:
1. O usuário acessa a área de chat na interface web.
2. O usuário digita uma pergunta (ex: "Quanto gastei com alimentação este mês?").
3. O sistema invoca o caso de uso UC-07 (Validar Segurança do Prompt).
4. O sistema encaminha a pergunta ao Agente Coach.
5. O Agente Coach consulta o banco de dados de transações.
6. O Agente Coach formula uma resposta com base nos dados.
7. O sistema exibe a resposta ao usuário.

**Pós-condições**: O usuário recebe uma resposta à sua pergunta.

**Fluxos Alternativos**:
- **FA-01**: Se a validação de segurança (UC-07) identificar um prompt malicioso, o sistema bloqueia a interação e exibe uma mensagem padrão de recusa.
- **FA-02**: Se não houver dados suficientes para responder à pergunta, o Agente Coach informa ao usuário que não há informações disponíveis.

---

### UC-04: Extrair Dados da Transação

**Descrição**: O Agente Extrator processa o texto da transação e extrai informações estruturadas.

**Ator Principal**: Sistema (Agente Extrator)

**Pré-condições**: Um texto de transação foi fornecido ao sistema.

**Fluxo Principal**:
1. O Agente Extrator recebe o texto da transação.
2. O Agente Extrator analisa o texto utilizando técnicas de processamento de linguagem natural.
3. O Agente Extrator identifica e extrai: valor, empresa e data.
4. O Agente Extrator formata os dados em um objeto JSON.
5. O Agente Extrator retorna o JSON ao orquestrador.

**Pós-condições**: Os dados da transação estão estruturados em formato JSON.

**Fluxos Alternativos**:
- **FA-01**: Se o texto não contiver as informações mínimas necessárias, o Agente Extrator retorna um erro ao orquestrador.

---

### UC-05: Classificar Transação

**Descrição**: O Agente Classificador determina a categoria da transação com base no nome da empresa.

**Ator Principal**: Sistema (Agente Classificador)

**Pré-condições**: Os dados estruturados da transação (JSON) foram gerados.

**Fluxo Principal**:
1. O Agente Classificador recebe o JSON com os dados da transação.
2. O Agente Classificador extrai o campo "empresa".
3. O Agente Classificador consulta uma ferramenta (API ou banco de dados mock) para determinar o nicho da empresa.
4. O Agente Classificador atribui uma categoria à transação (ex: "Alimentação").
5. O Agente Classificador adiciona o campo "categoria" ao JSON.
6. O Agente Classificador retorna o JSON atualizado ao orquestrador.

**Pós-condições**: A transação possui uma categoria associada.

**Fluxos Alternativos**:
- **FA-01**: Se a ferramenta não conseguir determinar a categoria, o Agente Classificador atribui a categoria padrão "Outros".

---

### UC-06: Armazenar Transação

**Descrição**: O sistema persiste os dados estruturados e classificados da transação no banco de dados.

**Ator Principal**: Sistema (Repositório de Transações)

**Pré-condições**: Os dados da transação foram extraídos e classificados.

**Fluxo Principal**:
1. O orquestrador recebe o JSON completo da transação.
2. O orquestrador invoca o Repositório de Transações.
3. O Repositório de Transações cria um novo registro no banco de dados com os dados da transação.
4. O Repositório de Transações confirma a operação ao orquestrador.

**Pós-condições**: A transação está armazenada no banco de dados.

**Fluxos Alternativos**:
- **FA-01**: Se houver um erro de banco de dados, o sistema registra o erro e informa ao usuário que a transação não pôde ser salva.

---

### UC-07: Validar Segurança do Prompt

**Descrição**: O Agente de Segurança analisa o prompt do usuário para identificar possíveis ameaças antes de encaminhá-lo ao Agente Coach.

**Ator Principal**: Sistema (Agente de Segurança)

**Pré-condições**: O usuário enviou uma pergunta ao Agente Coach.

**Fluxo Principal**:
1. O Agente de Segurança recebe o prompt do usuário.
2. O Agente de Segurança analisa o prompt em busca de padrões de prompt injection ou comportamentos indevidos.
3. O Agente de Segurança determina que o prompt é seguro.
4. O Agente de Segurança autoriza o encaminhamento do prompt ao Agente Coach.

**Pós-condições**: O prompt é considerado seguro e pode ser processado.

**Fluxos Alternativos**:
- **FA-01**: Se o Agente de Segurança identificar uma ameaça, ele bloqueia o prompt e retorna uma mensagem padrão de recusa ao usuário, sem encaminhar ao Agente Coach.

## 15. Diagrama Classes de Análise

O diagrama de classes de análise apresenta uma visão de alto nível das classes principais do sistema, organizadas segundo os estereótipos de **boundary** (fronteira), **control** (controle) e **entity** (entidade).

![Diagrama de Classes de Análise](diagrama_classes_analise.png)

**Descrição das Classes**:

- **InterfaceWeb** (Boundary): Representa a camada de apresentação do sistema, responsável por exibir formulários, dashboards e a interface de chat ao usuário.
- **OrquestradorAgentes** (Control): Classe central que coordena a comunicação e o fluxo de dados entre os diferentes agentes do sistema.
- **AgenteExtrator** (Control): Responsável por processar o texto da transação e extrair informações estruturadas.
- **AgenteClassificador** (Control): Responsável por classificar a transação em uma categoria, utilizando uma ferramenta externa.
- **AgenteSeguranca** (Control): Responsável por validar os prompts do usuário antes de encaminhá-los ao Agente Coach.
- **AgenteCoach** (Control): Responsável por interagir com o usuário, respondendo perguntas sobre suas finanças.
- **Transacao** (Entity): Representa uma transação financeira, contendo os atributos: id, valor, empresa, data e categoria.
- **RepositorioTransacoes** (Entity): Responsável por gerenciar a persistência e recuperação de objetos do tipo Transacao no banco de dados.

## 16. Diagrama de Interação

O diagrama de interação (também conhecido como diagrama de colaboração) ilustra o fluxo de mensagens entre os objetos do sistema durante o processamento de uma transação.

![Diagrama de Interação](diagrama_interacao.png)

**Descrição do Fluxo**:

O usuário inicia o processo colando o texto da transação na interface web. A interface encaminha o texto ao orquestrador, que coordena a execução sequencial dos agentes. O Agente Extrator analisa o texto e retorna um JSON estruturado. Em seguida, o Agente Classificador consulta uma ferramenta externa para determinar a categoria da empresa e retorna essa informação ao orquestrador. O orquestrador então cria um objeto de transação completo e solicita ao repositório que o armazene no banco de dados. Após a confirmação do salvamento, uma mensagem de sucesso é exibida ao usuário.

## 17. Diagrama de Atividade

O diagrama de atividade representa o fluxo de trabalho completo do processo de inserção e processamento de uma transação, incluindo os pontos de decisão e as partições de responsabilidade.

![Diagrama de Atividade](diagrama_atividade.png)

**Descrição das Partições**:

- **Agente Extrator**: Responsável por receber o texto, analisá-lo e extrair as informações estruturadas. Se os dados forem insuficientes, o processo é interrompido com uma mensagem de erro.
- **Agente Classificador**: Responsável por consultar a ferramenta de classificação e atribuir uma categoria à transação. Se nenhuma categoria for encontrada, a categoria padrão "Outros" é atribuída.
- **Persistência**: Responsável por criar o objeto de transação e salvá-lo no banco de dados. Em caso de falha, o erro é registrado e o processo é interrompido.

## 18. Diagrama de Estado

O diagrama de estado modela os diferentes estados pelos quais uma transação passa desde sua inserção até seu armazenamento final no sistema.

![Diagrama de Estado](diagrama_estado.png)

**Descrição dos Estados**:

- **Pendente**: Estado inicial quando o texto da transação é inserido pelo usuário.
- **EmExtracao**: A transação está sendo processada pelo Agente Extrator.
- **Extraida**: Os dados foram extraídos com sucesso e estão estruturados em JSON.
- **EmClassificacao**: A transação está sendo processada pelo Agente Classificador.
- **Classificada**: A categoria foi atribuída à transação.
- **EmPersistencia**: A transação está sendo salva no banco de dados.
- **Armazenada**: Estado final de sucesso, a transação está persistida e disponível para consulta.
- **Erro**: Estado final de falha, indicando que houve um problema em alguma etapa do processamento.

## 19. Diagrama de Sequência

O diagrama de sequência detalha a interação temporal entre os objetos do sistema durante o processo de consulta ao Agente Coach, incluindo a validação de segurança.

![Diagrama de Sequência](diagrama_sequencia.png)

**Descrição do Fluxo**:

O usuário digita uma pergunta na interface de chat. A interface encaminha a pergunta ao orquestrador, que primeiro a submete ao Agente de Segurança para validação. Se o prompt for considerado seguro, o orquestrador encaminha a pergunta ao Agente Coach. O Coach consulta o repositório de transações, que por sua vez acessa o banco de dados para recuperar as informações necessárias. Com os dados em mãos, o Coach calcula a resposta e a retorna ao orquestrador, que a encaminha à interface para exibição ao usuário. Se o prompt for identificado como malicioso, o Agente de Segurança retorna uma negativa, e uma mensagem padrão de recusa é exibida ao usuário sem que o Coach seja acionado.

## 20. DER e MER do Banco de Dados

### Diagrama de Entidade-Relacionamento (DER)

O DER apresenta a estrutura conceitual do banco de dados do sistema Moneytora, identificando as entidades principais, seus atributos e os relacionamentos entre elas.

![Diagrama DER](diagrama_der.png)

**Descrição das Entidades**:

- **Transacao**: Entidade central que armazena todas as transações financeiras processadas pelo sistema. Cada transação contém informações sobre o valor gasto, a empresa onde ocorreu a transação, a data e a categoria associada.

- **Categoria**: Entidade que representa as categorias de gastos predefinidas no sistema (ex: Alimentação, Transporte, Lazer). Esta tabela facilita a normalização dos dados e permite análises agregadas por categoria.

- **EmpresaClassificacao**: Entidade auxiliar que mapeia empresas conhecidas para suas respectivas categorias. Esta tabela é utilizada pelo Agente Classificador como uma ferramenta de lookup para classificação automática de transações.

**Descrição dos Relacionamentos**:

- Uma **Transacao** pertence a uma **Categoria** (relacionamento N:1).
- Uma **EmpresaClassificacao** está associada a uma **Categoria** (relacionamento N:1).

### Modelo de Entidade-Relacionamento (MER)

O MER detalha a implementação física do banco de dados, incluindo tipos de dados, chaves primárias, chaves estrangeiras e restrições de integridade. O script SQL completo está disponível no arquivo `modelo_mer.sql`.

**Estrutura das Tabelas**:

#### Tabela: Categoria

| Campo | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Identificador único da categoria |
| nome | VARCHAR(100) | NOT NULL, UNIQUE | Nome da categoria |
| descricao | TEXT | - | Descrição detalhada da categoria |

#### Tabela: EmpresaClassificacao

| Campo | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Identificador único do registro |
| nome_empresa | VARCHAR(200) | NOT NULL, UNIQUE | Nome da empresa |
| categoria_id | INTEGER | NOT NULL, FOREIGN KEY | Referência à categoria associada |

#### Tabela: Transacao

| Campo | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Identificador único da transação |
| valor | DECIMAL(10,2) | NOT NULL | Valor monetário da transação |
| empresa | VARCHAR(200) | NOT NULL | Nome da empresa/estabelecimento |
| data | DATE | NOT NULL | Data da transação |
| categoria | VARCHAR(100) | NOT NULL, FOREIGN KEY | Categoria da transação |
| data_criacao | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Data/hora de criação do registro |

**Índices Criados**:

- `idx_transacao_categoria`: Índice na coluna `categoria` da tabela `Transacao` para otimizar consultas de agregação por categoria.
- `idx_transacao_data`: Índice na coluna `data` da tabela `Transacao` para otimizar consultas de análise temporal.
- `idx_empresa_class_nome`: Índice na coluna `nome_empresa` da tabela `EmpresaClassificacao` para otimizar o lookup de classificação.

**Dados Iniciais (Seed Data)**:

O sistema será inicializado com as seguintes categorias padrão:

- Alimentação
- Transporte
- Lazer
- Saúde
- Educação
- Moradia
- Vestuário
- Tecnologia
- Outros

Exemplos de empresas pré-cadastradas para classificação automática incluem: McDonald's, iFood, Uber, Netflix, Drogasil e Amazon.

---

## Considerações Finais

Este documento apresenta uma visão completa e detalhada do projeto de software Moneytora, abrangendo desde a concepção inicial até a modelagem técnica necessária para o desenvolvimento. A arquitetura multiagente proposta representa uma abordagem inovadora para a gestão de finanças pessoais, combinando técnicas modernas de Inteligência Artificial com princípios sólidos de engenharia de software.

O foco do MVP na orquestração de agentes e na demonstração funcional do sistema permite validar a viabilidade técnica da solução dentro do prazo estabelecido, ao mesmo tempo em que estabelece uma base sólida para futuras expansões e melhorias. A documentação detalhada dos requisitos, casos de uso, diagramas UML e modelagem de banco de dados fornece um guia claro para a equipe de desenvolvimento, facilitando a divisão de tarefas e a coordenação entre os diferentes desenvolvedores.

Com este documento como referência, a equipe está preparada para iniciar o desenvolvimento do sistema Moneytora, com uma compreensão compartilhada dos objetivos, da arquitetura e das responsabilidades de cada componente do sistema.
