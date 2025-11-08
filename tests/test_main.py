"""Testes básicos da API Moneytora."""
from datetime import date
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import database
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def preparar_banco():
    """Garante que o banco de dados esteja limpo antes de cada teste."""

    database.Base.metadata.drop_all(bind=database.engine)
    database.Base.metadata.create_all(bind=database.engine)
    yield
    database.Base.metadata.drop_all(bind=database.engine)
    database.Base.metadata.create_all(bind=database.engine)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Moneytora API is running"}


def test_processar_transacao_sucesso(monkeypatch):
    texto_transacao = "Compra de R$ 55,90 no iFood em 15/08/2024"

    def _fake_invoke(_inputs):
        return {"transacao_id": 42}

    monkeypatch.setattr("app.main.app_graph.invoke", _fake_invoke)

    response = client.post(
        "/api/transacoes/processar",
        json={"texto": texto_transacao},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["transacao_id"] == 42


def test_crud_transacoes():
    payload = {
        "valor": 55.9,
        "empresa": "iFood",
        "data": date(2024, 8, 15).isoformat(),
        "categoria": "Alimentação",
    }

    response = client.post("/api/transacoes/", json=payload)
    assert response.status_code == 200
    transacao = response.json()
    transacao_id = transacao["id"]

    response = client.get(f"/api/transacoes/{transacao_id}")
    assert response.status_code == 200
    assert response.json()["empresa"] == "iFood"

    response = client.get("/api/transacoes/")
    assert response.status_code == 200
    assert any(item["id"] == transacao_id for item in response.json())

    update_payload = {"categoria": "Delivery"}
    response = client.put(
        f"/api/transacoes/{transacao_id}", json=update_payload
    )
    assert response.status_code == 200
    assert response.json()["categoria"] == "Delivery"

    response = client.delete(f"/api/transacoes/{transacao_id}")
    assert response.status_code == 200
    assert response.json()["id"] == transacao_id

    response = client.get(f"/api/transacoes/{transacao_id}")
    assert response.status_code == 404


def test_dashboard_gastos_por_categoria():
    transacoes = [
        {
            "valor": 100.0,
            "empresa": "Uber",
            "data": date(2024, 8, 10).isoformat(),
            "categoria": "Transporte",
        },
        {
            "valor": 50.0,
            "empresa": "Netflix",
            "data": date(2024, 8, 11).isoformat(),
            "categoria": "Lazer",
        },
        {
            "valor": 25.0,
            "empresa": "Uber",
            "data": date(2024, 8, 12).isoformat(),
            "categoria": "Transporte",
        },
    ]

    for transacao in transacoes:
        response = client.post("/api/transacoes/", json=transacao)
        assert response.status_code == 200

    response = client.get("/api/dashboard/gastos-por-categoria")
    assert response.status_code == 200
    dados = response.json()
    totais = {item["categoria"]: item["total"] for item in dados}
    assert totais["Transporte"] == 125.0
    assert totais["Lazer"] == 50.0
