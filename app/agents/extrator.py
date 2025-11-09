"""Agente responsável por extrair dados estruturados de uma notificação financeira."""
from datetime import date
from functools import lru_cache

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GOOGLE_API_KEY


class DadosTransacao(BaseModel):
    """Estrutura da saída esperada pelo agente extrator."""

    valor: float = Field(description="O valor numérico da transação.")
    empresa: str = Field(description="O nome da empresa ou estabelecimento.")
    data: date = Field(description="A data da transação no formato AAAA-MM-DD.")


# Parser responsável por transformar a saída do LLM em um objeto ``DadosTransacao``.
output_parser = PydanticOutputParser(pydantic_object=DadosTransacao)

prompt_template = """
Você é um especialista em extrair informações financeiras de textos.
Analise o texto a seguir e extraia o valor, a empresa e a data da transação.
Se a data não especificar o ano, assuma o ano corrente.

{format_instructions}

Texto da transação:
{texto_transacao}
"""

prompt = ChatPromptTemplate.from_template(
    template=prompt_template,
    partial_variables={"format_instructions": output_parser.get_format_instructions()},
)


def _build_llm() -> ChatGoogleGenerativeAI:
    """Cria uma instância do modelo Gemini configurada para o extrator."""

    if not GOOGLE_API_KEY:
        raise EnvironmentError(
            "GOOGLE_API_KEY não configurada. Configure a variável de ambiente para utilizar o agente extrator."
        )
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)


# Encadeamos prompt -> modelo -> parser utilizando a sintaxe de pipe do LangChain.
@lru_cache(maxsize=1)
def _get_chain():
    return prompt | _build_llm() | output_parser


def extrair_dados_transacao(texto: str) -> DadosTransacao:
    """Executa o agente extrator para obter os dados estruturados de uma transação."""

    return _get_chain().invoke({"texto_transacao": texto})
