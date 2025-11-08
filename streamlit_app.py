"""Interface Streamlit para o sistema Moneytora."""
from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd
import streamlit as st

from app.agents.coach import responder_pergunta
from app.agents.seguranca import avaliar_mensagem
from app.config import GOOGLE_API_KEY
from app.graph.orchestrator import app_graph
from app.repository import (
    calcular_gastos_por_categoria,
    criar_transacao,
    listar_transacoes,
)
from app.schemas import TransacaoCreate
from app.database import session_scope


st.set_page_config(page_title="Moneytora", layout="wide")
st.title("Moneytora – Monitoramento Financeiro com Agentes de IA")
st.caption(
    "Automatize o processamento de transações, visualize seus gastos e converse com o coach financeiro."
)


def _mostrar_alerta_chave_api() -> None:
    """Exibe um aviso caso a Google API Key não esteja configurada."""

    if not GOOGLE_API_KEY:
        st.warning(
            "Configure a variável de ambiente `GOOGLE_API_KEY` para habilitar os agentes "
            "de extração, segurança e coach financeiro."
        )


def _executar_fluxo_processamento(texto: str) -> dict[str, object]:
    """Executa o LangGraph e retorna o estado final, tratando exceções."""

    try:
        return app_graph.invoke({"texto_original": texto})
    except EnvironmentError as exc:
        raise RuntimeError(
            "Não foi possível executar o fluxo automático. "
            "Verifique se a `GOOGLE_API_KEY` está configurada."
        ) from exc
    except Exception as exc:  # pragma: no cover - defensivo
        raise RuntimeError(f"Falha inesperada durante o processamento: {exc}") from exc


def _carregar_transacoes() -> list:
    """Carrega transações cadastradas no banco para exibição."""

    with session_scope() as session:
        return listar_transacoes(session, limit=500)


def _registrar_transacao_manualmente(dados: TransacaoCreate) -> None:
    """Persiste uma transação informada manualmente."""

    with session_scope() as session:
        criar_transacao(session, dados)


def _carregar_gastos_por_categoria() -> Iterable:
    """Recupera os totais agregados por categoria."""

    with session_scope() as session:
        return calcular_gastos_por_categoria(session)


def aba_processar_notificacoes() -> None:
    """Exibe a aba de processamento automático de notificações."""

    st.subheader("Processamento Automático de Notificações")
    st.write(
        "Cole abaixo o texto bruto de uma notificação financeira. "
        "O Moneytora irá extrair as informações relevantes, classificar a categoria "
        "e armazenar a transação automaticamente."
    )

    with st.form("form_processar_texto", clear_on_submit=False):
        texto = st.text_area(
            "Texto da notificação",
            placeholder=(
                "Exemplo: \"Compra aprovada no valor de R$ 58,90 no Uber em 23/07 às 20h.\""
            ),
            height=200,
        )
        enviar = st.form_submit_button("Processar transação")

    if not enviar:
        return

    if not texto.strip():
        st.info("Insira o texto da notificação para continuar.")
        return

    with st.spinner("Executando agentes..."):
        try:
            resultado = _executar_fluxo_processamento(texto.strip())
        except RuntimeError as exc:
            st.error(str(exc))
            return

    if erro := resultado.get("erro"):
        st.error(f"Não foi possível concluir o processamento: {erro}")
        return

    st.success("Transação processada com sucesso!")
    st.write(
        {
            "Transação ID": resultado.get("transacao_id"),
            "Empresa": resultado.get("empresa"),
            "Valor": resultado.get("valor"),
            "Data": str(resultado.get("data")),
            "Categoria": resultado.get("categoria"),
        }
    )


def aba_transacoes() -> None:
    """Aba dedicada ao cadastro manual e listagem das transações."""

    st.subheader("Cadastro Manual de Transações")
    with st.form("form_cadastro_manual", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
            data_transacao = st.date_input("Data da transação", value=date.today())
        with col2:
            empresa = st.text_input("Empresa/Estabelecimento")
            categoria = st.text_input("Categoria", placeholder="Ex: Alimentação, Transporte...")
        cadastrar = st.form_submit_button("Salvar transação manualmente")

    if cadastrar:
        if not empresa or not categoria:
            st.warning("Informe a empresa e a categoria para salvar a transação.")
        else:
            dados_transacao = TransacaoCreate(
                valor=float(valor),
                empresa=empresa.strip(),
                data=data_transacao,
                categoria=categoria.strip() or "Outros",
            )
            try:
                _registrar_transacao_manualmente(dados_transacao)
            except Exception as exc:  # pragma: no cover - operações de IO
                st.error(f"Erro ao salvar transação: {exc}")
            else:
                st.success("Transação cadastrada com sucesso!")

    st.divider()
    st.subheader("Transações Registradas")
    transacoes = _carregar_transacoes()

    if not transacoes:
        st.info("Nenhuma transação cadastrada até o momento.")
        return

    dados_tabela = [
        {
            "ID": item.id,
            "Data": item.data.strftime("%d/%m/%Y"),
            "Empresa": item.empresa,
            "Categoria": item.categoria,
            "Valor (R$)": round(float(item.valor or 0), 2),
            "Cadastro": item.data_criacao.strftime("%d/%m/%Y %H:%M"),
        }
        for item in transacoes
    ]
    df = pd.DataFrame(dados_tabela)
    st.dataframe(df, use_container_width=True, hide_index=True)


def aba_dashboard() -> None:
    """Exibe gráficos simples com base nas transações armazenadas."""

    st.subheader("Visão Geral de Gastos por Categoria")
    dados = list(_carregar_gastos_por_categoria())

    if not dados:
        st.info("Cadastre algumas transações para visualizar o dashboard.")
        return

    df = pd.DataFrame(
        {
            "Categoria": [item.categoria for item in dados],
            "Total": [round(float(item.total or 0), 2) for item in dados],
        }
    ).set_index("Categoria")

    st.bar_chart(df, use_container_width=True)
    st.write(df)


def aba_coach() -> None:
    """Interface de chat com o agente coach financeiro."""

    st.subheader("Coach Financeiro")
    st.write(
        "Converse com o agente coach para obter insights sobre seus gastos. "
        "Todas as perguntas passam pelo agente de segurança antes de chegar ao coach."
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for mensagem in st.session_state.chat_history:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    pergunta = st.chat_input("Envie uma pergunta sobre suas finanças")
    if not pergunta:
        return

    st.session_state.chat_history.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    try:
        classificacao = avaliar_mensagem(pergunta)
    except EnvironmentError:
        st.error(
            "O agente de segurança não está disponível. "
            "Verifique a configuração da `GOOGLE_API_KEY`."
        )
        return
    except Exception as exc:  # pragma: no cover - defensivo
        st.error(f"Falha ao avaliar a mensagem: {exc}")
        return

    if classificacao != "seguro":
        resposta = (
            "Sua mensagem foi classificada como maliciosa pelo agente de segurança "
            "e, portanto, foi bloqueada."
        )
        st.session_state.chat_history.append({"role": "assistant", "content": resposta})
        with st.chat_message("assistant"):
            st.markdown(resposta)
        return

    try:
        resposta = responder_pergunta(pergunta)
    except EnvironmentError:
        st.error(
            "O agente coach não está disponível no momento. "
            "Verifique a configuração da `GOOGLE_API_KEY`."
        )
        return
    except Exception as exc:  # pragma: no cover - depende de serviços externos
        st.error(f"Falha ao obter resposta do coach: {exc}")
        return

    st.session_state.chat_history.append({"role": "assistant", "content": resposta})
    with st.chat_message("assistant"):
        st.markdown(resposta)


_mostrar_alerta_chave_api()

abas = {
    "Processar Notificação": aba_processar_notificacoes,
    "Transações": aba_transacoes,
    "Dashboard": aba_dashboard,
    "Coach Financeiro": aba_coach,
}

selecionada = st.sidebar.radio("Navegação", list(abas.keys()))
abas[selecionada]()

