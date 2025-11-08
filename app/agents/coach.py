"""Agente coach financeiro responsável por responder perguntas sobre as finanças."""
from functools import lru_cache

try:
    from langchain.agents import create_sql_agent
except ImportError:  # pragma: no cover - depende da versão instalada
    create_sql_agent = None
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase

from app.config import GOOGLE_API_KEY
from app.database import DATABASE_URL

try:  # Compatibilidade com diferentes versões do LangChain
    from langchain.agents import AgentType

    AGENT_TYPE = AgentType.ZERO_SHOT_REACT_DESCRIPTION
except (ImportError, AttributeError):  # pragma: no cover - depende da versão instalada
    AGENT_TYPE = "zero-shot-react-description"

_db = SQLDatabase.from_uri(DATABASE_URL)


def _build_llm() -> ChatGoogleGenerativeAI:
    if not GOOGLE_API_KEY:
        raise EnvironmentError(
            "GOOGLE_API_KEY não configurada. Configure a variável de ambiente para utilizar o agente coach."
        )
    # O modelo é compartilhado com os demais agentes para manter consistência de respostas.
    return ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY)


@lru_cache(maxsize=1)
def _get_agent_executor():
    if create_sql_agent is None:
        raise EnvironmentError(
            "Dependências do LangChain para o agente coach não estão disponíveis na versão instalada."
        )

    llm = _build_llm()
    toolkit = SQLDatabaseToolkit(db=_db, llm=llm)
    return create_sql_agent(llm=llm, toolkit=toolkit, agent_type=AGENT_TYPE, verbose=False)


def responder_pergunta(pergunta: str) -> str:
    """Executa o agente coach retornando a resposta textual ao usuário."""

    agente = _get_agent_executor()
    resultado = agente.invoke({"input": pergunta})
    if isinstance(resultado, dict):
        return str(resultado.get("output") or resultado)
    return str(resultado)
