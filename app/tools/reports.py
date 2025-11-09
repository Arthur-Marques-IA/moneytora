import os
import sqlite3
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple

import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Caminho padrão do banco (ajuste conforme seu projeto)
DEFAULT_DB_PATH = os.getenv("MONEYTORA_DB_PATH", "moneytora.db")

# Pasta de saída para relatórios
REPORTS_DIR = os.getenv("MONEYTORA_REPORTS_DIR", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def _parse_date(value: str) -> date:
    # aceita '2025-11-09' ou '09/11/2025'
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return datetime.strptime(value, "%d/%m/%Y").date()


def _get_connection(db_path: str):
    return sqlite3.connect(db_path)


def _fetch_transactions(
    start_date: date,
    end_date: date,
    cliente_id: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Tuple]:
    """
    Busca transações no SQLite.
    Assumo que a tabela se chame 'Transacao' e tenha:
    id, valor, empresa, data, categoria
    Se você tiver um campo de dono/usuário, filtre por ele também.
    """
    conn = _get_connection(db_path)
    cursor = conn.cursor()

    # Ajuste aqui se tiver coluna de usuário, ex: WHERE cliente_id = ?
    if cliente_id:
        query = """
            SELECT id, valor, empresa, data, categoria
            FROM Transacao
            WHERE date(data) BETWEEN ? AND ?
              AND cliente_id = ?
            ORDER BY date(data) ASC
        """
        cursor.execute(query, (start_date.isoformat(), end_date.isoformat(), cliente_id))
    else:
        query = """
            SELECT id, valor, empresa, data, categoria
            FROM Transacao
            WHERE date(data) BETWEEN ? AND ?
            ORDER BY date(data) ASC
        """
        cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))

    rows = cursor.fetchall()
    conn.close()
    return rows


def _separate_in_out(rows: List[Tuple]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Dependendo do teu modelo, pode ser que 'valor' seja sempre positivo
    e você use 'categoria' para saber se é despesa.
    Aqui vou assumir a regra simples:
    - valor < 0 -> saída
    - valor > 0 -> entrada
    Se o seu banco sempre grava positivo e usa categoria, adapte aqui.
    """
    entradas = []
    saidas = []
    for (id_, valor, empresa, data_, categoria) in rows:
        item = {
            "id": id_,
            "valor": float(valor),
            "empresa": empresa,
            "data": data_,
            "categoria": categoria,
        }
        if item["valor"] >= 0:
            entradas.append(item)
        else:
            saidas.append(item)
    return {"entradas": entradas, "saidas": saidas}


def _aggregate_by_category(transacoes: List[Dict[str, Any]]) -> Dict[str, float]:
    agg = {}
    for t in transacoes:
        cat = t.get("categoria") or "Outros"
        # valor pode ser negativo nas saídas
        agg[cat] = agg.get(cat, 0) + t["valor"]
    return agg


def _detect_outliers(transacoes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Outlier bem simples usando IQR.
    """
    if not transacoes:
        return []

    valores = [abs(t["valor"]) for t in transacoes]
    valores_sorted = sorted(valores)
    n = len(valores_sorted)

    def percentile(p):
        k = (n - 1) * p
        f = int(k)
        c = min(f + 1, n - 1)
        if f == c:
            return valores_sorted[int(k)]
        d0 = valores_sorted[f] * (c - k)
        d1 = valores_sorted[c] * (k - f)
        return d0 + d1

    q1 = percentile(0.25)
    q3 = percentile(0.75)
    iqr = q3 - q1
    lim_sup = q3 + 1.5 * iqr

    outliers = [t for t in transacoes if abs(t["valor"]) > lim_sup]
    return outliers


def _plot_pie_by_category(saidas_by_cat: Dict[str, float], out_path: str):
    if not saidas_by_cat:
        return
    labels = list(saidas_by_cat.keys())
    # converter para positivo
    sizes = [abs(v) for v in saidas_by_cat.values()]

    plt.figure()
    plt.pie(sizes, labels=labels, autopct="%1.1f%%")
    plt.title("Distribuição de despesas por categoria")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def _plot_bar_cashflow(dias: List[str], entradas: List[float], saidas: List[float], out_path: str):
    if not dias:
        return
    x = range(len(dias))
    plt.figure()
    plt.bar(x, entradas, label="Entradas")
    plt.bar(x, [-s for s in saidas], bottom=entradas, label="Saídas")  # empilhado simples
    plt.xticks(x, dias, rotation=45)
    plt.legend()
    plt.title("Fluxo diário de caixa")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def _build_pdf(
    output_path: str,
    periodo: str,
    resumo: Dict[str, Any],
    pie_path: Optional[str] = None,
    cashflow_path: Optional[str] = None,
):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Cabeçalho
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 40, "Relatório Financeiro")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 55, f"Período: {periodo}")
    c.drawString(40, height - 70, f"Total de entradas: R$ {resumo['total_entradas']:.2f}")
    c.drawString(40, height - 85, f"Total de saídas: R$ {resumo['total_saidas']:.2f}")
    c.drawString(40, height - 100, f"Saldo do período: R$ {resumo['saldo']:.2f}")

    y = height - 120

    # Maiores despesas
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Maiores despesas:")
    y -= 15
    c.setFont("Helvetica", 10)
    for item in resumo["top_saidas"][:5]:
        c.drawString(
            50,
            y,
            f"- {item['empresa']} ({item['categoria']}) R$ {abs(item['valor']):.2f} em {item['data']}",
        )
        y -= 12

    y -= 10

    # Maiores entradas
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Maiores entradas:")
    y -= 15
    c.setFont("Helvetica", 10)
    for item in resumo["top_entradas"][:5]:
        c.drawString(
            50,
            y,
            f"- {item['empresa']} R$ {item['valor']:.2f} em {item['data']}",
        )
        y -= 12

    y -= 10

    # Outliers
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Transações atípicas (outliers):")
    y -= 15
    c.setFont("Helvetica", 10)
    if resumo["outliers"]:
        for item in resumo["outliers"]:
            c.drawString(
                50,
                y,
                f"- {item['empresa']} ({item['categoria']}) R$ {abs(item['valor']):.2f} em {item['data']}",
            )
            y -= 12
    else:
        c.drawString(50, y, "- Nenhuma transação atípica identificada.")
        y -= 12

    # Nova página para gráficos
    c.showPage()

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, height - 40, "Gráficos")

    graph_y = height - 80

    if pie_path and os.path.exists(pie_path):
        img = ImageReader(pie_path)
        c.drawImage(img, 40, graph_y - 200, width=250, height=200, preserveAspectRatio=True)

    if cashflow_path and os.path.exists(cashflow_path):
        img2 = ImageReader(cashflow_path)
        c.drawImage(img2, 300, graph_y - 200, width=250, height=200, preserveAspectRatio=True)

    c.save()


def gerar_relatorio_gastos(
    start_date: str,
    end_date: str,
    cliente_id: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """
    Gera relatório financeiro em PDF e devolve metadados para o agente.
    - start_date, end_date: 'YYYY-MM-DD' ou 'DD/MM/YYYY'
    """
    sd = _parse_date(start_date)
    ed = _parse_date(end_date)

    rows = _fetch_transactions(sd, ed, cliente_id=cliente_id, db_path=db_path)

    if not rows:
        return {
            "ok": False,
            "mensagem": "Não há transações no período informado.",
            "pdf_path": None,
        }

    sep = _separate_in_out(rows)
    entradas = sep["entradas"]
    saidas = sep["saidas"]

    total_entradas = sum(t["valor"] for t in entradas)
    total_saidas = sum(abs(t["valor"]) for t in saidas)
    saldo = total_entradas - total_saidas

    # agregação por categoria (para despesas)
    saidas_by_cat = _aggregate_by_category(saidas)

    # topo
    top_saidas = sorted(saidas, key=lambda x: abs(x["valor"]), reverse=True)
    top_entradas = sorted(entradas, key=lambda x: x["valor"], reverse=True)

    # outliers
    outliers = _detect_outliers(saidas)

    # gráfico de pizza
    pie_path = os.path.join(REPORTS_DIR, f"pie_{sd}_{ed}.png")
    _plot_pie_by_category(saidas_by_cat, pie_path)

    # gráfico de fluxo diário
    # agrupa por dia
    daily = {}
    for t in entradas + saidas:
        d = t["data"]
        v = t["valor"]
        if d not in daily:
            daily[d] = {"entradas": 0.0, "saidas": 0.0}
        if v >= 0:
            daily[d]["entradas"] += v
        else:
            daily[d]["saidas"] += abs(v)

    dias = sorted(daily.keys())
    entradas_diarias = [daily[d]["entradas"] for d in dias]
    saidas_diarias = [daily[d]["saidas"] for d in dias]

    cashflow_path = os.path.join(REPORTS_DIR, f"cashflow_{sd}_{ed}.png")
    _plot_bar_cashflow(dias, entradas_diarias, saidas_diarias, cashflow_path)

    # monta pdf
    pdf_name = f"relatorio_financeiro_{sd}_{ed}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_name)

    resumo = {
        "total_entradas": total_entradas,
        "total_saidas": total_saidas,
        "saldo": saldo,
        "top_saidas": top_saidas,
        "top_entradas": top_entradas,
        "outliers": outliers,
    }

    periodo_label = f"{sd.strftime('%d/%m/%Y')} a {ed.strftime('%d/%m/%Y')}"
    _build_pdf(pdf_path, periodo_label, resumo, pie_path=pie_path, cashflow_path=cashflow_path)

    # mensagem curta para o coach usar
    texto_resumo = (
        f"Análise do período {periodo_label}:\n"
        f"- Entradas: R$ {total_entradas:.2f}\n"
        f"- Saídas: R$ {total_saidas:.2f}\n"
        f"- Saldo: R$ {saldo:.2f}\n"
        f"- Maior despesa: "
        f"{top_saidas[0]['empresa']} (R$ {abs(top_saidas[0]['valor']):.2f}) em {top_saidas[0]['data']}"
        if top_saidas else ""
    )

    return {
        "ok": True,
        "mensagem": texto_resumo,
        "pdf_path": pdf_path,
        "periodo": periodo_label,
        "totais": {
            "entradas": total_entradas,
            "saidas": total_saidas,
            "saldo": saldo,
        },
        "top_saidas": top_saidas,
        "top_entradas": top_entradas,
        "outliers": outliers,
    }
