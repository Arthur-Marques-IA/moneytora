"""Camada de acesso a dados centralizada para operações com transações."""
from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import database, schemas


def criar_transacao(db: Session, transacao: schemas.TransacaoCreate) -> database.Transacao:
    """Persiste uma nova transação e retorna a instância armazenada."""

    db_transacao = database.Transacao(**transacao.model_dump())
    db.add(db_transacao)
    db.commit()
    db.refresh(db_transacao)
    return db_transacao


def listar_transacoes(db: Session, skip: int = 0, limit: int = 100) -> List[database.Transacao]:
    """Retorna uma lista paginada de transações cadastradas."""

    return db.query(database.Transacao).offset(skip).limit(limit).all()


def obter_transacao(db: Session, transacao_id: int) -> Optional[database.Transacao]:
    """Obtém uma transação pelo identificador."""

    return db.query(database.Transacao).filter(database.Transacao.id == transacao_id).first()


def atualizar_transacao(
    db: Session, transacao_id: int, dados: schemas.TransacaoUpdate
) -> Optional[database.Transacao]:
    """Atualiza uma transação existente com os dados informados."""

    db_transacao = obter_transacao(db, transacao_id)
    if not db_transacao:
        return None

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(db_transacao, campo, valor)

    db.commit()
    db.refresh(db_transacao)
    return db_transacao


def deletar_transacao(db: Session, transacao_id: int) -> Optional[database.Transacao]:
    """Remove uma transação do banco de dados e retorna o registro excluído."""

    db_transacao = obter_transacao(db, transacao_id)
    if db_transacao:
        db.delete(db_transacao)
        db.commit()
    return db_transacao


def calcular_gastos_por_categoria(db: Session) -> List[schemas.GastoPorCategoria]:
    """Agrega o total de gastos por categoria."""

    resultados: Iterable[tuple[str, float]] = (
        db.query(
            database.Transacao.categoria,
            func.sum(database.Transacao.valor).label("total"),
        )
        .group_by(database.Transacao.categoria)
        .all()
    )
    return [
        schemas.GastoPorCategoria(categoria=categoria, total=float(total or 0))
        for categoria, total in resultados
    ]
