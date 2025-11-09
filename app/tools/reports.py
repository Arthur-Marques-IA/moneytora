import os
import sqlite3
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from langchain.tools import tool


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
    Assumo que a tabela se chame 'transacoes' e tenha:
    id, valor, empresa, data, categoria
    Se você tiver um campo de dono/usuário, filtre por ele também.
    """
    conn = _get_connection(db_path)
    cursor = conn.cursor()

    # Ajuste aqui se tiver coluna de usuário, ex: WHERE cliente_id = ?
    if cliente_id:
        query = """
            SELECT id, valor, empresa, data, categoria
            FROM transacoes
            WHERE date(data) BETWEEN ? AND ?
              AND cliente_id = ?
            ORDER BY date(data) ASC
        """
        cursor.execute(query, (start_date.isoformat(), end_date.isoformat(), cliente_id))
    else:
        query = """
            SELECT id, valor, empresa, data, categoria
            FROM transacoes
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

from typing import Optional, Dict, Any
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

@tool
def gerar_relatorio_financeiro(
    start_date: str,
    end_date: str,
    cliente_id: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """Gera um relatório financeiro em PDF para o período especificado.
    
    Args:
        start_date: Data de início no formato 'YYYY-MM-DD'
        end_date: Data de fim no formato 'YYYY-MM-DD'
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

    saidas_by_cat = _aggregate_by_category(saidas)
    top_saidas = sorted(saidas, key=lambda x: abs(x["valor"]), reverse=True)
    top_entradas = sorted(entradas, key=lambda x: x["valor"], reverse=True)
    outliers = _detect_outliers(saidas)

    # Caminhos para salvar gráficos e PDF
    REPORTS_DIR = r"C:\Users\pedro\OneDrive\hack_akcit\moneytora\reports"
    os.makedirs(REPORTS_DIR, exist_ok=True)

    pie_path = os.path.join(REPORTS_DIR, f"pie_{sd}_{ed}.png")
    _plot_pie_by_category(saidas_by_cat, pie_path)

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

    # ==========================================================
    # PDF ESTILIZADO - MONEYTORA (com nomes de estilo únicos)
    # ==========================================================
    LOGO_PATH = r"C:\Users\pedro\OneDrive\hack_akcit\moneytora\moneytora_1.jpg"
    PRIMARY_COLOR = "#1E90FF"

    def _build_pdf(pdf_path, periodo_label, resumo, pie_path=None, cashflow_path=None):
        """Gera PDF estilizado com a identidade visual da Moneytora."""
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title="Relatório Financeiro - Moneytora",
        )

        styles = getSampleStyleSheet()
        # Usar nomes exclusivos para evitar conflito com estilos existentes
        styles.add(ParagraphStyle(
            name="MTitle",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor(PRIMARY_COLOR),
            spaceAfter=12,
            alignment=1,
        ))
        styles.add(ParagraphStyle(
            name="MSubTitle",
            fontSize=12,
            leading=14,
            textColor=colors.grey,
            spaceAfter=8,
            alignment=1,
        ))
        styles.add(ParagraphStyle(
            name="MHeading",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor(PRIMARY_COLOR),
            spaceBefore=12,
            spaceAfter=6,
        ))
        styles.add(ParagraphStyle(
            name="MNormal",
            fontSize=11,
            leading=15,
            textColor=colors.black,
        ))

        elementos = []

        # Cabeçalho: logo (se existir) + títulos
        if os.path.exists(LOGO_PATH):
            try:
                elementos.append(Image(LOGO_PATH, width=120, height=60))
            except Exception:
                # caso o arquivo exista mas não seja legível, ignore o logo
                pass

        elementos.append(Spacer(1, 6))
        elementos.append(Paragraph("Relatório Financeiro", styles["MTitle"]))
        elementos.append(Paragraph("Moneytora", styles["MSubTitle"]))
        elementos.append(Paragraph(f"Período: {periodo_label}", styles["MNormal"]))
        elementos.append(Spacer(1, 12))

        # Resumo financeiro
        elementos.append(Paragraph("Resumo Financeiro", styles["MHeading"]))
        data_resumo = [
            ["Entradas", f"R$ {resumo['total_entradas']:.2f}"],
            ["Saídas", f"R$ {resumo['total_saidas']:.2f}"],
            ["Saldo", f"R$ {resumo['saldo']:.2f}"],
        ]

        tabela = Table(data_resumo, colWidths=[6*cm, 6*cm])
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY_COLOR)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(PRIMARY_COLOR)),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elementos.append(tabela)
        elementos.append(Spacer(1, 12))

        # Gráficos
        if pie_path and os.path.exists(pie_path):
            elementos.append(Paragraph("Distribuição de Despesas por Categoria", styles["MHeading"]))
            elementos.append(Image(pie_path, width=400, height=250))
            elementos.append(Spacer(1, 12))

        if cashflow_path and os.path.exists(cashflow_path):
            elementos.append(Paragraph("Fluxo de Caixa Diário", styles["MHeading"]))
            elementos.append(Image(cashflow_path, width=400, height=250))
            elementos.append(Spacer(1, 12))

        # Principais despesas
        if resumo.get("top_saidas"):
            elementos.append(Paragraph("Principais Despesas", styles["MHeading"]))
            top_data = [["Empresa", "Valor (R$)", "Data"]]
            for t in resumo["top_saidas"][:5]:
                top_data.append([t.get("empresa", ""), f"{abs(t['valor']):.2f}", t.get("data", "")])

            tabela_top = Table(top_data, colWidths=[6*cm, 3*cm, 3*cm])
            tabela_top.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY_COLOR)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elementos.append(tabela_top)
            elementos.append(Spacer(1, 20))

        # Rodapé
        elementos.append(Paragraph("<b>Moneytora</b> © 2025 - Inteligência Financeira", styles["MNormal"]))

        # Gera PDF
        doc.build(elementos)

    # Chama o builder de PDF estilizado
    _build_pdf(pdf_path, periodo_label, resumo, pie_path=pie_path, cashflow_path=cashflow_path)

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
