"""
Tool: Consultar Dados Financeiros

Esta tool permite ao Agente Coach consultar o banco de dados de transações
para responder perguntas sobre gastos, categorias, períodos e valores.
"""

from langchain.tools import tool, ToolRuntime

from app.agents.sql_consultor import responder_pergunta as consultar_sql_agent


@tool
def consultar_dados_financeiros(pergunta: str, runtime: ToolRuntime) -> str:
    """Consulta o banco de dados de transações financeiras para responder perguntas sobre gastos, categorias, períodos e valores.
    
    Use esta ferramenta quando o usuário perguntar sobre:
    - Valores gastos (ex: "quanto gastei em alimentação?")
    - Maiores despesas (ex: "quais foram minhas 5 maiores compras?")
    - Gastos por categoria (ex: "mostre meus gastos por categoria")
    - Gastos em períodos específicos (ex: "quanto gastei em outubro?")
    - Comparações (ex: "gastei mais este mês ou no mês passado?")
    - Listagem de transações (ex: "liste todas as minhas compras no iFood")
    - Totais e somas (ex: "qual foi meu gasto total este mês?")
    
    A ferramenta aceita linguagem natural e entende referências temporais como:
    - "este mês", "mês passado", "últimos 30 dias"
    - "em outubro", "no ano de 2024"
    - "ontem", "na semana passada"
    
    Args:
        pergunta: A pergunta do usuário sobre seus dados financeiros em linguagem natural
        runtime: Contexto de execução (injetado automaticamente, não visível para o LLM)
    
    Returns:
        Resposta textual com os dados solicitados, formatada de forma clara e legível
    
    Examples:
        >>> consultar_dados_financeiros("Quanto gastei com alimentação este mês?")
        "Seus gastos com alimentação este mês foram de R$ 450,00, distribuídos em 12 transações."
        
        >>> consultar_dados_financeiros("Quais foram minhas 3 maiores despesas?")
        "Suas 3 maiores despesas foram: 1. Aluguel - R$ 1.200,00..."
    """
    try:
        # Chama o agente SQL existente
        resultado = consultar_sql_agent(pergunta)
        
        if not resultado or resultado.strip() == "":
            return (
                "Não encontrei dados para essa consulta. "
                "Tente especificar o período (ex: 'neste mês', 'em outubro', 'nos últimos 30 dias') "
                "ou a categoria que deseja consultar."
            )
        
        return resultado
        
    except Exception as e:
        return f"Não consegui consultar os dados no momento. Erro: {str(e)}"
