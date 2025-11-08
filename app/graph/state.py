"""Estrutura de estado compartilhado entre os nós do LangGraph."""
from datetime import date
from typing import Optional, TypedDict


class GraphState(TypedDict, total=False):
    texto_original: str
    valor: Optional[float]
    empresa: Optional[str]
    data: Optional[date]
    categoria: Optional[str]
    transacao_id: Optional[int]
    erro: Optional[str]
