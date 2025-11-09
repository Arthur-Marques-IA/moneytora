"""
Agente Coach: responsável pela conversação com o usuário e orquestração de consultas financeiras.
Ele pode:
1. Responder dúvidas gerais de educação financeira.
2. Consultar o agente SQL para perguntas sobre valores/categorias/períodos.
3. Acionar uma tool que gera relatório de gastos.
"""

from typing import Literal, TypedDict, Optional

from app.agents.sql_consultation import responder_pergunta as consultar_sql
from app.config import GOOGLE_API_KEY

# opcional: uma tool que gera relatório de gastos
try:
    from app.tools.reports import gerar_relatorio_financeiro
except Exception:
    gerar_relatorio_financeiro = None  # se não existir, o agente só não usa

from langchain_google_genai import ChatGoogleGenerativeAI


# Prompt base do coach
COACH_SYSTEM_PROMPT = (
    ''' Você é a "Moneytora", uma assistente de finanças pessoais e coach de IA. Sua personalidade é encorajadora, profissional e objetiva.\n\nSua missão principal é ajudar o usuário a entender seus hábitos financeiros com base exclusivamente nos dados de transações fornecidos.\n\n---\n\n### 1. Diretrizes de Interação\n\n* Tom de Voz: Seja amigável, mas direto ao ponto. Use uma linguagem clara e evite jargões financeiros complexos. Aja como um coach que quer ver o usuário ter sucesso.\n* Fonte da Verdade: Suas respostas devem ser 100% baseadas nos dados de transações fornecidos. NUNCA invente transações, valores ou categorias. Se o usuário perguntar sobre algo que não está nos dados, informe que você não tem essa informação.\n* Proatividade (Leve): Ao responder uma pergunta, sinta-se à vontade para adicionar uma observação útil.\n * Exemplo de Usuário: "Quanto gastei com alimentação?"\n * Sua Resposta: "Este mês, seus gastos registrados em 'Alimentação' foram de R$ 450,00. Notei que a maior parte disso foi na categoria 'Restaurantes'."\n\n### 2. Contexto de Dados\n\nVocê terá acesso a uma lista de transações do usuário. Esses dados já foram extraídos e classificados. Os dados estarão em um formato de lista de objetos, como este:\n\njson\n[\n {\n \"id\": 1,\n \"descricao\": \"Mc Donald's\",\n \"valor\": 50.00,\n \"data\": \"2025-10-25\",\n \"categoria\": \"Alimentação\"\n },\n {\n \"id\": 2,\n \"descricao\": \"Uber Viagem\",\n \"valor\": 25.50,\n \"data\": \"2025-10-26\",\n \"categoria\": \"Transporte\"\n },\n {\n \"id\": 3,\n \"descricao\": \"Netflix\",\n \"valor\": 39.90,\n \"data\": \"2025-10-27\",\n \"categoria\": \"Assinaturas\"\n }\n]\n\n\n*(Nota: Na implementação real, esta lista será injetada dinamicamente no contexto da conversa.)\n\n### 3. Capacidades (O que você DEVE fazer)\n\n Responder a Perguntas Específicas:\n * "Quanto gastei em [categoria] este mês?"\n * "Quais foram minhas 5 maiores despesas?"\n * "Liste todas as minhas compras em [loja]."\n* Fazer Resumos:\n * "Faça um resumo dos meus gastos da última semana."\n * "Quais são minhas principais categorias de gastos?"\n* Identificar Padrões (Simples):\n * "Onde gastei mais dinheiro?"\n * "Quais assinaturas eu paguei este mês?"\n* Referenciar os Gráficos:\n * "Como você pode ver no gráfico de pizza, 'Alimentação' foi sua maior despesa..."\n\n### 4. Limitações e Guardrails (O que você NÃO DEVE fazer)\n\n* NÃO DÊ ACONSELHAMENTO FINANCEIRO (REGRA DE OURO):\n * Permitido (Coaching): "Notei que 30% dos seus gastos foram em 'Restaurantes'. Esta é uma área comum onde as pessoas buscam economizar."\n * PROIBIDO (Aconselhamento): "Você deve parar de comer fora."\n * PROIBIDO (Investimentos): "Você deve investir em ações" ou "Compre Bitcoin."\n * Sua resposta padrão para isso deve ser: "Como uma IA de coaching, não posso dar conselhos financeiros ou de investimento. Minha função é ajudá-lo a organizar e entender seus gastos."\n* NÃO FAÇA PREVISÕES: Não tente prever gastos futuros ou o mercado de ações.\n* NÃO SEJA CRÍTICO OU SENTENCIOSO: Nunca julgue os gastos do usuário (ex: "Você gastou muito com isso."). Mantenha um tom neutro e focado nos dados.\n* NÃO DISCUTA OUTROS ASSUNTOS: Se o usuário perguntar sobre o tempo, política ou qualquer outro tópico não relacionado às finanças pessoais dele (baseado nos dados), reoriente educadamente a conversa.\n * Exemplo: "Meu foco é ajudá-lo com seus dados financeiros. Você tem alguma pergunta sobre suas transações?" '''
)


# Estrutura para a classificação de intenção
class Intencao(TypedDict):
    tipo: Literal["consultar_sql", "gerar_relatorio", "resposta_geral"]
    # você pode acrescentar mais campos aqui, tipo período, categoria etc.


def _get_llm() -> ChatGoogleGenerativeAI:
    if not GOOGLE_API_KEY:
        raise RuntimeError("Erro: GOOGLE_API_KEY não configurada.")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2,
    )


def classificar_intencao(mensagem: str) -> Intencao:
    """
    Usa o LLM para entender o que o usuário quer fazer.
    Retorna um dicionário simples com o tipo de ação.
    """
    llm = _get_llm()

    prompt_classificador = f"""
Você é um classificador de intenções para um chatbot financeiro.

Classifique a mensagem a seguir em UMA das opções:
1. "consultar_sql" -> quando o usuário quer saber valores, totais, maiores gastos, gastos por categoria, por mês, por dia, por período, comparação de gastos.
2. "gerar_relatorio" -> quando o usuário pedir relatório, resumo completo, pdf, documento, relatório detalhado dos gastos.
3. "resposta_geral" -> quando o usuário pedir dicas de economia, como se organizar, como guardar mais, como sair das dívidas, sem pedir números específicos.

Responda APENAS com o nome da intenção, nada mais.

Mensagem do usuário: \"{mensagem}\"
"""

    resposta = llm.invoke(prompt_classificador)
    texto = str(resposta).strip().lower()

    if "consultar_sql" in texto:
        return {"tipo": "consultar_sql"}
    if "gerar_relatorio" in texto:
        return {"tipo": "gerar_relatorio"}
    # fallback
    return {"tipo": "resposta_geral"}


def _responder_geral(mensagem: str) -> str:
    """
    Usa o LLM com o prompt do coach para responder perguntas abertas de finanças pessoais.
    """
    llm = _get_llm()
    prompt = (
        f"{COACH_SYSTEM_PROMPT}\n"
        f"Usuário: {mensagem}\n"
        f"Coach (responda em português, com 3 a 6 tópicos práticos se fizer sentido):"
    )
    resposta = llm.invoke(prompt)
    return str(resposta).strip()


def _responder_com_sql(mensagem: str) -> str:
    """
    Encapsula a chamada ao agente SQL e formata o retorno.
    """
    try:
        dados = consultar_sql(mensagem)
        if not dados:
            return (
                "Não encontrei dados para essa consulta. "
                "Tente especificar o período (ex: 'neste mês', 'em outubro', 'nos últimos 30 dias') ou a categoria."
            )
        # aqui você pode padronizar a resposta do agente SQL
        return f"Aqui está o que encontrei:\n{dados}"
    except Exception as e:
        return f"Não consegui consultar seus dados agora. Detalhes técnicos: {e}"


def _responder_com_relatorio(mensagem: str, cliente_id: Optional[str] = None) -> str:
    """
    Chama a tool de relatório, se existir.
    """
    if gerar_relatorio_financeiro is None:
        # fallback se a tool não estiver disponível
        return (
            "Você pediu um relatório de gastos. No momento, a ferramenta de relatório não está disponível. "
            "Mas posso te mostrar um resumo se você disser o período (ex: 'relatório de outubro')."
        )

    try:
        # se o relatório precisar de um id, use o parâmetro; senão, remova
        relatorio = gerar_relatorio_financeiro(cliente_id or "")
        return (
            "Aqui está o relatório de gastos que gerei para você:\n"
            f"{relatorio}\n"
            "Se quiser, posso te ajudar a interpretar."
        )
    except Exception as e:
        return f"Tentei gerar o relatório, mas houve um erro: {e}"


def responder_pergunta(mensagem: str, cliente_id: Optional[str] = None) -> str:
    """
    Ponto de entrada do agente.
    1. Classifica a intenção.
    2. Executa a ação (SQL, relatório ou resposta geral).
    3. Devolve a resposta ao usuário.
    """
    if not GOOGLE_API_KEY:
        return "Erro: GOOGLE_API_KEY não configurada."

    intencao = classificar_intencao(mensagem)

    if intencao["tipo"] == "consultar_sql":
        return _responder_com_sql(mensagem)

    if intencao["tipo"] == "gerar_relatorio":
        return _responder_com_relatorio(mensagem, cliente_id=cliente_id)

    # caso contrário, resposta geral
    return _responder_geral(mensagem)
