"""Definição do grafo de orquestração responsável pelo processamento das transações."""
from langgraph.graph import END, StateGraph

from app.agents.extrator import extrair_dados_transacao
from app.database import session_scope
from app import repository, schemas
from app.tools.classificacao_tool import classificar_empresa_por_categoria

from .state import GraphState


# -----------------------
# Nós do LangGraph
# -----------------------

def node_extrair_dados(state: GraphState) -> GraphState:
    """Executa o agente extrator e atualiza o estado com os dados estruturados."""

    try:
        dados = extrair_dados_transacao(state["texto_original"])
        state.update(dados.model_dump())
    except Exception as exc:  # pragma: no cover - depende do LLM
        state["erro"] = f"Falha na extração: {exc}"
    return state


def node_classificar(state: GraphState) -> GraphState:
    """Classifica a empresa em uma categoria utilizando a ferramenta dedicada."""

    if state.get("erro"):
        return state

    empresa = state.get("empresa")
    if not empresa:
        state["erro"] = "Empresa não identificada para classificação."
        return state

    try:
        categoria = classificar_empresa_por_categoria.invoke(empresa)
        state["categoria"] = categoria
    except Exception as exc:  # pragma: no cover - defensivo
        state["erro"] = f"Falha na classificação: {exc}"
    return state


def node_persistir(state: GraphState) -> GraphState:
    """Persiste a transação extraída no banco de dados SQLite."""

    if state.get("erro"):
        return state

    try:
        valor = state.get("valor")
        data = state.get("data")
        categoria = state.get("categoria")
        empresa = state.get("empresa")
        if valor is None or data is None or categoria is None or not empresa:
            state["erro"] = "Dados insuficientes para persistir a transação."
            return state

        with session_scope() as session:
            dados_transacao = schemas.TransacaoCreate(
                valor=valor,
                empresa=empresa,
                data=data,
                categoria=categoria,
            )
            nova_transacao = repository.criar_transacao(session, dados_transacao)
            state["transacao_id"] = nova_transacao.id
    except Exception as exc:  # pragma: no cover - operações de IO
        state["erro"] = f"Falha na persistência: {exc}"
    return state


# -----------------------
# Regras de transição
# -----------------------

def deve_continuar(state: GraphState) -> str:
    """Define se o fluxo deve prosseguir para a persistência ou encerrar."""

    return "__end__" if state.get("erro") else "persistir_dados"


# -----------------------
# Construção do grafo
# -----------------------

workflow = StateGraph(GraphState)
workflow.add_node("extrair_dados", node_extrair_dados)
workflow.add_node("classificar_categoria", node_classificar)
workflow.add_node("persistir_dados", node_persistir)

workflow.set_entry_point("extrair_dados")
workflow.add_edge("extrair_dados", "classificar_categoria")
workflow.add_conditional_edges(
    "classificar_categoria",
    deve_continuar,
    {"persistir_dados": "persistir_dados", "__end__": END},
)
workflow.add_edge("persistir_dados", END)

# ``compile`` converte a definição declarativa acima em uma aplicação executável.
app_graph = workflow.compile()
