"""Ferramentas auxiliares utilizadas pelos agentes do Moneytora."""
from langchain.tools import tool

from app.database import EmpresaClassificacao, session_scope

CATEGORIAS_MOCK = {
    "ifood": "Alimentação",
    "uber": "Transporte",
    "netflix": "Lazer",
    "amazon": "Compras",
    "mcdonald's": "Alimentação",
}


@tool
def classificar_empresa_por_categoria(empresa: str) -> str:
    """Classifica a empresa consultando o histórico e aplicando um fallback.

    O fluxo prioriza as classificações já conhecidas no banco de dados para
    garantir consistência. Caso a empresa ainda não tenha sido classificada,
    utilizamos um mapeamento mockado simples como fallback e registramos o
    resultado encontrado para aprendizados futuros.
    """

    empresa_lower = empresa.lower()

    with session_scope() as db:
        classificacao = (
            db.query(EmpresaClassificacao)
            .filter(EmpresaClassificacao.nome_empresa == empresa_lower)
            .first()
        )
        if classificacao:
            return classificacao.categoria

    for key, categoria in CATEGORIAS_MOCK.items():
        if key in empresa_lower:
            with session_scope() as db:
                existente = (
                    db.query(EmpresaClassificacao)
                    .filter(EmpresaClassificacao.nome_empresa == empresa_lower)
                    .first()
                )
                if existente is None:
                    db.add(
                        EmpresaClassificacao(
                            nome_empresa=empresa_lower,
                            categoria=categoria,
                        )
                    )
            return categoria

    with session_scope() as db:
        existente = (
            db.query(EmpresaClassificacao)
            .filter(EmpresaClassificacao.nome_empresa == empresa_lower)
            .first()
        )
        if existente is None:
            db.add(
                EmpresaClassificacao(
                    nome_empresa=empresa_lower,
                    categoria="Outros",
                )
            )

    return "Outros"
