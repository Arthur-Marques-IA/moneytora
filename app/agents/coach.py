"""Agente coach financeiro responsável por responder perguntas sobre as finanças."""
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI
try:
    from langchain_community.agent_toolkits.sql.base import create_sql_agent
except ImportError:  # pragma: no cover - depende da versão instalada
    try:
        from langchain.agents import create_sql_agent
    except ImportError:  # pragma: no cover - compatibilidade
        create_sql_agent = None
try:
    from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
except ImportError:  # pragma: no cover - depende da versão instalada
    try:
        from langchain.agents.agent_toolkits import SQLDatabaseToolkit
    except ImportError:  # pragma: no cover - compatibilidade
        SQLDatabaseToolkit = None
from langchain_community.utilities import SQLDatabase

from app.config import GOOGLE_API_KEY
from app.database import DATABASE_URL

_db = SQLDatabase.from_uri(DATABASE_URL)


def _build_llm() -> ChatGoogleGenerativeAI:
    if not GOOGLE_API_KEY:
        raise EnvironmentError(
            "GOOGLE_API_KEY não configurada. Configure a variável de ambiente para utilizar o agente coach."
        )
    # O modelo é compartilhado com os demais agentes para manter consistência de respostas.
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)


@lru_cache(maxsize=1)
def _get_agent_executor():
    if create_sql_agent is None or SQLDatabaseToolkit is None:
        raise EnvironmentError(
            "Dependências do LangChain para o agente coach não estão disponíveis na versão instalada."
        )

    llm = _build_llm()
    toolkit = SQLDatabaseToolkit(db=_db, llm=llm)
    return create_sql_agent(llm=llm, toolkit=toolkit, verbose=False)


def responder_pergunta(pergunta: str) -> str:
    """Executa o agente coach retornando a resposta textual ao usuário."""

    agente = _get_agent_executor()
    resultado = agente.invoke({"input": pergunta})
    if isinstance(resultado, dict):
        return str(resultado.get("output") or resultado)
    return str(resultado)
