"""Modelos Pydantic utilizados pelos endpoints da API."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TransacaoBase(BaseModel):
    valor: float
    empresa: str
    data: date
    categoria: str


class TransacaoCreate(TransacaoBase):
    """Schema utilizado para criação de novas transações manualmente."""


class TransacaoUpdate(BaseModel):
    valor: Optional[float] = None
    empresa: Optional[str] = None
    data: Optional[date] = None
    categoria: Optional[str] = None


class TransacaoSchema(TransacaoBase):
    id: int
    data_criacao: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessarTextoRequest(BaseModel):
    texto: str


class ChatRequest(BaseModel):
    pergunta: str


class GastoPorCategoria(BaseModel):
    categoria: str
    total: float
