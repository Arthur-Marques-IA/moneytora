"""Configuração do banco de dados e modelos ORM."""
from __future__ import annotations

import datetime
from contextlib import contextmanager

from sqlalchemy import Column, Date, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = "sqlite:///./moneytora.db"

# O parâmetro ``check_same_thread`` é necessário quando utilizamos SQLite com aplicações
# assíncronas como o FastAPI, permitindo o compartilhamento da conexão entre threads.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Transacao(Base):
    """Representa uma transação financeira armazenada pelo Moneytora."""

    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    valor = Column(Float, nullable=False)
    empresa = Column(String, nullable=False)
    data = Column(Date, nullable=False)
    categoria = Column(String, nullable=False, index=True)
    data_criacao = Column(DateTime, default=datetime.datetime.utcnow)


class EmpresaClassificacao(Base):
    """Mapeamento entre o nome da empresa e a categoria identificada."""

    __tablename__ = "empresa_classificacao"

    id = Column(Integer, primary_key=True)
    nome_empresa = Column(String, unique=True, index=True)
    categoria = Column(String, nullable=False)


# Criamos as tabelas automaticamente durante o bootstrap da aplicação.
Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Fornece uma sessão de banco para uso em endpoints FastAPI."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Session:
    """Fornece um gerenciador de contexto para operações fora dos endpoints."""

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
