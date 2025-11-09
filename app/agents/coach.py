"""
Módulo do agente coach de finanças pessoais "Moneytora". 
Este agente utiliza ferramentas para consultar dados financeiros e gerar relatórios, 
além de responder perguntas gerais sobre educação financeira.
"""

from typing import Optional

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage

from app.config import GOOGLE_API_KEY
from app.tools.reports import gerar_relatorio_financeiro
from app.tools.sql_consultation import consultar_dados_financeiros


# ============================================================================
# PROMPT DO SISTEMA
# ============================================================================

COACH_SYSTEM_PROMPT = """Você é a "Moneytora", uma assistente de finanças pessoais e coach de IA. Sua personalidade é encorajadora, profissional e objetiva.

Sua missão principal é ajudar o usuário a entender seus hábitos financeiros com base exclusivamente nos dados de transações fornecidos.

## Diretrizes de Interação

* **Tom de Voz**: Seja amigável, mas direto ao ponto. Use uma linguagem clara e evite jargões financeiros complexos. Aja como um coach que quer ver o usuário ter sucesso.

* **Fonte da Verdade**: Suas respostas devem ser 100% baseadas nos dados de transações fornecidos. NUNCA invente transações, valores ou categorias. Se o usuário perguntar sobre algo que não está nos dados, informe que você não tem essa informação.

* **Proatividade (Leve)**: Ao responder uma pergunta, sinta-se à vontade para adicionar uma observação útil.
  - Exemplo: "Este mês, seus gastos registrados em 'Alimentação' foram de R$ 450,00. Notei que a maior parte disso foi na categoria 'Restaurantes'."

## Capacidades

Você tem acesso a ferramentas que permitem:
1. **Consultar dados financeiros**: Use a tool `consultar_dados_financeiros` para responder perguntas sobre valores, totais, gastos por categoria, períodos, etc.
2. **Gerar relatórios**: Use a tool `gerar_relatorio_pdf` quando o usuário pedir um relatório completo, PDF ou documento detalhado.
3. **Responder dúvidas gerais**: Para dicas de organização financeira, economia e educação financeira (sem dar conselhos de investimento).

## Limitações e Guardrails

* **NÃO DÊ ACONSELHAMENTO FINANCEIRO** (REGRA DE OURO):
  - ✅ Permitido (Coaching): "Notei que 30% dos seus gastos foram em 'Restaurantes'. Esta é uma área comum onde as pessoas buscam economizar."
  - ❌ PROIBIDO (Aconselhamento): "Você deve parar de comer fora."
  - ❌ PROIBIDO (Investimentos): "Você deve investir em ações" ou "Compre Bitcoin."
  - Resposta padrão: "Como uma IA de coaching, não posso dar conselhos financeiros ou de investimento. Minha função é ajudá-lo a organizar e entender seus gastos."

* **NÃO FAÇA PREVISÕES**: Não tente prever gastos futuros ou o mercado de ações.

* **NÃO SEJA CRÍTICO OU SENTENCIOSO**: Nunca julgue os gastos do usuário. Mantenha um tom neutro e focado nos dados.

* **NÃO DISCUTA OUTROS ASSUNTOS**: Se o usuário perguntar sobre temas não relacionados às finanças pessoais, reoriente educadamente a conversa.
"""


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def _get_llm() -> ChatGoogleGenerativeAI:
    """Cria uma instância do modelo Gemini configurada para o coach."""
    if not GOOGLE_API_KEY:
        raise RuntimeError("Erro: GOOGLE_API_KEY não configurada.")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2,
    )


# ============================================================================
# CRIAÇÃO DO AGENTE
# ============================================================================

def create_coach_agent():
    """
    Cria e retorna o agente coach usando create_agent do LangChain.
    
    Esta é a abordagem moderna recomendada, que permite ao LLM decidir
    autonomamente qual tool usar com base nas descrições.
    
    Returns:
        Agente coach configurado e pronto para uso
    """
    # Lista de tools disponíveis (importadas do módulo app.tools.coach)
    tools = [
        consultar_dados_financeiros,
        gerar_relatorio_financeiro,
    ]
    
    # Cria o agente
    agent = create_agent(
        model=_get_llm(),
        tools=tools,
        system_prompt=COACH_SYSTEM_PROMPT,
    )
    
    return agent


# ============================================================================
# INTERFACE PÚBLICA 
# ============================================================================

# Cache do agente para evitar recriação
_cached_agent = None


def responder_pergunta(mensagem: str, cliente_id: Optional[str] = None) -> str:
    """
    Ponto de entrada do agente coach (mantém compatibilidade com a API anterior).
    
    Esta função processa a mensagem do usuário e retorna uma resposta do agente coach.
    O agente pode decidir autonomamente usar ferramentas (consultar dados, gerar relatórios)
    ou responder diretamente com base em seu conhecimento de educação financeira.
    
    Args:
        mensagem: Pergunta ou solicitação do usuário
        cliente_id: ID opcional do cliente (usado para filtrar dados por usuário)
    
    Returns:
        Resposta do agente coach em formato de texto
    
    Examples:
        >>> responder_pergunta("Quanto gastei com alimentação este mês?")
        "Seus gastos com alimentação este mês foram de R$ 450,00..."
        
        >>> responder_pergunta("Gere um relatório do mês passado")
        "✅ Relatório gerado com sucesso para o período de 01/10/2024 a 31/10/2024!..."
        
        >>> responder_pergunta("Como posso economizar mais?")
        "Aqui estão algumas dicas práticas para economizar: 1. Acompanhe seus gastos..."
    """
    global _cached_agent
    
    if not GOOGLE_API_KEY:
        return "Erro: GOOGLE_API_KEY não configurada."
    
    try:
        # Cria ou reutiliza o agente
        if _cached_agent is None:
            _cached_agent = create_coach_agent()
        
        # Prepara o contexto (se houver cliente_id)
        context = {"cliente_id": cliente_id} if cliente_id else {}
        
        # Invoca o agente
        resultado = _cached_agent.invoke(
            {"messages": [("user", mensagem)]},
            config={"configurable": {"context": context}}
        )
        
        # Extrai a resposta
        if isinstance(resultado, dict) and "messages" in resultado:
            # Pega a última mensagem do agente
            last_message = resultado["messages"][-1]
            if isinstance(last_message, AIMessage):
                return last_message.content
            return str(last_message)
        
        return str(resultado)
        
    except Exception as e:
        return f"Ocorreu um erro ao processar sua pergunta: {str(e)}"


def limpar_cache_agente():
    """
    Limpa o cache do agente, forçando sua recriação na próxima invocação.
    
    Útil quando há mudanças nas configurações ou quando se deseja liberar memória.
    """
    global _cached_agent
    _cached_agent = None

