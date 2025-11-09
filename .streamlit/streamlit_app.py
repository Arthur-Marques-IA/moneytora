"""Interface Streamlit para o sistema Moneytora."""
from __future__ import annotations

from datetime import date
from typing import List

import pandas as pd
import streamlit as st
import os
import sys


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.agents.coach import responder_pergunta
from app.agents.seguranca import avaliar_mensagem
from app.config import GOOGLE_API_KEY, GROQ_API
from app.graph.orchestrator import app_graph
from app.repository import (
    calcular_gastos_por_categoria,
    criar_transacao,
    listar_transacoes,
)
from app.schemas import GastoPorCategoria, TransacaoCreate, TransacaoSchema
from app.database import session_scope
import base64
import requests
from PyPDF2 import PdfReader

st.set_page_config(page_title="Moneytora", layout="wide", page_icon='💵')
st.title("Moneytora – Monitoramento Financeiro com Agentes de IA")
st.caption(
    "Automatize o processamento de transações, visualize seus gastos e converse com o coach financeiro."
)


def _formatar_moeda(valor: float) -> str:
    """Formata valores monetários no padrão brasileiro simples."""

    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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


def _carregar_transacoes() -> List[TransacaoSchema]:
    """Carrega transações cadastradas no banco para exibição."""

    with session_scope() as session:
        registros = listar_transacoes(session, limit=500)
        return [TransacaoSchema.model_validate(registro) for registro in registros]


def _registrar_transacao_manualmente(dados: TransacaoCreate) -> None:
    """Persiste uma transação informada manualmente."""

    with session_scope() as session:
        criar_transacao(session, dados)


def _carregar_gastos_por_categoria() -> List[GastoPorCategoria]:
    """Recupera os totais agregados por categoria."""

    with session_scope() as session:
        dados = calcular_gastos_por_categoria(session)
        return [GastoPorCategoria.model_validate(item) for item in dados]


API_URL = "https://api.groq.com/openai/v1/chat/completions"

def extrair_texto_imagem_groq(arquivo) -> str:
    """Extrai texto de uma imagem usando a Groq API (modelo multimodal)."""
    conteudo = arquivo.read()
    b64 = base64.b64encode(conteudo).decode("utf-8")

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "system",
                "content": "Você é um OCR inteligente. Extraia todo o texto legível da imagem enviada e devolva apenas o texto puro."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": { "url": f"data:image/png;base64,{b64}" }
                    },
                    {
                        "type": "text",
                        "text": "Extraia o texto desta imagem."
                    }
                ]
            }
        ],
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "max_completion_tokens": 1024
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API}",
        "Content-Type": "application/json"
    }

    resp = requests.post(API_URL, headers=headers, json=payload)

    if resp.status_code != 200:
        raise RuntimeError(f"Erro ao chamar Groq API: {resp.status_code} {resp.text}")

    res_json = resp.json()
    if "choices" not in res_json or not res_json["choices"]:
        raise RuntimeError(f"Resposta inesperada da Groq API: {res_json}")

    mensagem = res_json["choices"][0]["message"]
    return mensagem.get("content", "").strip()

def extrair_texto_pdf_groq(arquivo):
    """Extrai texto de um PDF localmente (rápido)"""
    reader = PdfReader(arquivo)
    texto = "\n".join(page.extract_text() or "" for page in reader.pages)
    return texto.strip()

def extrair_texto_ofx(arquivo):
    """Lê arquivo OFX (texto simples)"""
    return arquivo.read().decode("utf-8")

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
        arquivo = st.file_uploader(
            "Ou envie um arquivo (imagem, PDF ou OFX):",
            type=["jpg", "jpeg", "png", "pdf", "ofx"]
        )
        enviar = st.form_submit_button("Processar transação")

    if not enviar:
        return

    
    if not texto.strip() and not arquivo:
        st.info("Insira o texto ou envie um arquivo para continuar.")
        return

    # Se o usuário enviou um arquivo, extrair o texto antes de processar
    if arquivo:
        with st.spinner("Extraindo texto do arquivo..."):
            if arquivo.type in ["image/jpeg", "image/png"]:
                texto_extraido = extrair_texto_imagem_groq(arquivo)
            elif arquivo.type == "application/pdf":
                texto_extraido = extrair_texto_pdf_groq(arquivo)
            elif arquivo.name.endswith(".ofx"):
                texto_extraido = extrair_texto_ofx(arquivo)
            else:
                st.error("Tipo de arquivo não suportado.")
                return

            texto = texto_extraido or ""

    with st.spinner("Executando agentes..."):
        try:
            print(texto_extraido)
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
    st.dataframe(df, width='stretch', hide_index=True)


def aba_dashboard() -> None:
    """Exibe gráficos e insights detalhados sobre as transações."""

    st.subheader("Visão Geral de Gastos")
    transacoes = _carregar_transacoes()

    if not transacoes:
        st.info("Cadastre algumas transações para visualizar o dashboard.")
        return

    df_transacoes = pd.DataFrame(
        [
            {
                "id": item.id,
                "data": pd.to_datetime(item.data),
                "categoria": item.categoria,
                "empresa": item.empresa,
                "valor": float(item.valor or 0),
            }
            for item in transacoes
        ]
    )

    totais_categoria = (
        df_transacoes.groupby("categoria", as_index=False)["valor"]
        .sum()
        .sort_values("valor", ascending=False)
    )
    total_gasto = df_transacoes["valor"].sum()
    ticket_medio = df_transacoes["valor"].mean() if not df_transacoes.empty else 0
    categoria_principal = (
        totais_categoria.iloc[0]
        if not totais_categoria.empty
        else {"categoria": "N/A", "valor": 0}
    )

    df_transacoes["mes"] = df_transacoes["data"].dt.to_period("M")
    gastos_mensais = (
        df_transacoes.groupby("mes", as_index=False)["valor"]
        .sum()
        .sort_values("mes")
    )
    mes_atual_valor = gastos_mensais.iloc[-1]["valor"] if not gastos_mensais.empty else 0
    delta_mensal = ""
    if len(gastos_mensais) >= 2:
        valor_anterior = gastos_mensais.iloc[-2]["valor"]
        diferenca = mes_atual_valor - valor_anterior
        if valor_anterior > 0:
            percentual = (diferenca / valor_anterior) * 100
            delta_mensal = f"{percentual:+.1f}%"
        else:
            delta_mensal = "n/d"

    col1, col2, col3 = st.columns(3)
    col1.metric("Total acumulado", _formatar_moeda(total_gasto), f"{len(transacoes)} transações")
    col2.metric("Ticket médio", _formatar_moeda(ticket_medio))
    col3.metric(
        "Gasto do último mês",
        _formatar_moeda(mes_atual_valor),
        delta=delta_mensal or None,
    )

    st.markdown("#### Distribuição de gastos por categoria")
    st.bar_chart(
        totais_categoria.set_index("categoria"),
        width='stretch',
    )

    col_graficos_1, col_graficos_2 = st.columns(2)

    with col_graficos_1:
        st.markdown("##### Evolução mensal de gastos")
        if not gastos_mensais.empty:
            mensal_plot = gastos_mensais.copy()
            mensal_plot["mes"] = mensal_plot["mes"].astype(str)
            st.line_chart(
                mensal_plot.set_index("mes"),
                width='stretch',
            )
        else:
            st.info("Ainda não há dados suficientes para a visão mensal.")

    with col_graficos_2:
        st.markdown("##### Tendência diária de gastos")
        gastos_diarios = (
            df_transacoes.groupby("data", as_index=False)["valor"]
            .sum()
            .sort_values("data")
        )
        st.area_chart(
            gastos_diarios.set_index("data"),
            width='stretch',
        )

    st.markdown("#### Insights automáticos")
    insights = []
    if total_gasto:
        insights.append(
            f"- Categoria com maior gasto: **{categoria_principal['categoria']}** "
            f"({_formatar_moeda(categoria_principal['valor'])})."
        )
    if len(transacoes) > 1:
        top_empresas = (
            df_transacoes.groupby("empresa", as_index=False)["valor"]
            .sum()
            .sort_values("valor", ascending=False)
            .head(3)
        )
        ranking_empresas = ", ".join(
            f"{linha['empresa']} ({_formatar_moeda(linha['valor'])})"
            for _, linha in top_empresas.iterrows()
        )
        insights.append(f"- Principais estabelecimentos consumidores: {ranking_empresas}.")
    if delta_mensal:
        insights.append(
            "- O último mês apresentou variação de "
            f"{delta_mensal.replace('+', '+ ').replace('-', '- ')} em relação ao anterior."
        )
    if not insights:
        insights.append("- Cadastre mais transações para obter insights detalhados.")
    for insight in insights:
        st.markdown(insight)

    st.markdown("#### Transações recentes")
    recentes = df_transacoes.sort_values("data", ascending=False).head(10)
    recentes_formatado = recentes.assign(
        data=recentes["data"].dt.strftime("%d/%m/%Y"),
        valor=recentes["valor"].map(_formatar_moeda),
    )[["data", "empresa", "categoria", "valor"]]
    st.dataframe(recentes_formatado, width='stretch', hide_index=True)


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