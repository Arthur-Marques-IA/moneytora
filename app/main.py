"""Aplicação FastAPI que expõe os fluxos do Moneytora."""
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.agents.coach import responder_pergunta
from app.agents.seguranca import avaliar_mensagem
from app.graph.orchestrator import app_graph
from app import database, repository, schemas
from app.schemas import ChatRequest, ProcessarTextoRequest

app = FastAPI(
    title="Moneytora API",
    description="API para gestão financeira pessoal com agentes de IA.",
    version="1.0.0",
)


@app.get("/")
def read_root() -> dict[str, str]:
    """Endpoint de verificação simples utilizado pelo monitoramento."""

    return {"status": "Moneytora API is running"}


@app.post("/api/transacoes/processar")
def processar_transacao(request: ProcessarTextoRequest) -> dict[str, object]:
    """Processa um texto de notificação financeira utilizando o LangGraph."""

    inputs = {"texto_original": request.texto}
    final_state = app_graph.invoke(inputs)

    if final_state.get("erro"):
        raise HTTPException(status_code=400, detail=final_state["erro"])

    return {
        "success": True,
        "transacao_id": final_state.get("transacao_id"),
        "mensagem": "Transação processada e armazenada com sucesso.",
    }


@app.post("/api/transacoes/", response_model=schemas.TransacaoSchema)
def create_transacao(
    transacao: schemas.TransacaoCreate,
    db: Session = Depends(database.get_db),
) -> schemas.TransacaoSchema:
    """Cria uma nova transação manualmente."""

    return repository.criar_transacao(db, transacao)


@app.get("/api/transacoes/", response_model=List[schemas.TransacaoSchema])
def get_transacoes(
    skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)
) -> List[schemas.TransacaoSchema]:
    """Lista transações cadastradas com suporte a paginação simples."""

    return repository.listar_transacoes(db, skip=skip, limit=limit)


@app.get("/api/transacoes/{transacao_id}", response_model=schemas.TransacaoSchema)
def get_transacao(
    transacao_id: int, db: Session = Depends(database.get_db)
) -> schemas.TransacaoSchema:
    """Recupera uma transação específica pelo identificador."""

    db_transacao = repository.obter_transacao(db, transacao_id=transacao_id)
    if db_transacao is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return db_transacao


@app.put("/api/transacoes/{transacao_id}", response_model=schemas.TransacaoSchema)
def update_transacao(
    transacao_id: int,
    transacao: schemas.TransacaoUpdate,
    db: Session = Depends(database.get_db),
) -> schemas.TransacaoSchema:
    """Atualiza uma transação existente."""

    db_transacao = repository.atualizar_transacao(db, transacao_id, transacao)
    if db_transacao is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return db_transacao


@app.delete("/api/transacoes/{transacao_id}", response_model=schemas.TransacaoSchema)
def delete_transacao(
    transacao_id: int, db: Session = Depends(database.get_db)
) -> schemas.TransacaoSchema:
    """Remove uma transação existente."""

    db_transacao = repository.deletar_transacao(db, transacao_id=transacao_id)
    if db_transacao is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return db_transacao


@app.get(
    "/api/dashboard/gastos-por-categoria",
    response_model=List[schemas.GastoPorCategoria],
)
def get_gastos_por_categoria(
    db: Session = Depends(database.get_db),
) -> List[schemas.GastoPorCategoria]:
    """Retorna o total de gastos agrupados por categoria."""

    return repository.calcular_gastos_por_categoria(db)


@app.post("/api/chat")
def chat_financeiro(request: ChatRequest) -> dict[str, object]:
    """Fluxo de chat com validação de segurança antes da execução do coach financeiro."""

    try:
        classificacao = avaliar_mensagem(request.pergunta)
    except EnvironmentError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if classificacao != "seguro":
        return {
            "success": False,
            "mensagem": "Sua mensagem foi bloqueada pelo sistema de segurança.",
            "classificacao": classificacao,
        }

    try:
        resposta = responder_pergunta(request.pergunta)
    except EnvironmentError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"success": True, "resposta": resposta}
