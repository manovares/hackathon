from __future__ import annotations

import streamlit as st

from cost_calculator import CostInput, calcular_custos
from edital_analyzer import analyze_edital_text
from search_service import SearchQuery, search_properties


def _fmt_brl(value: float) -> str:
    try:
        v = float(value)
    except Exception:
        v = 0.0
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R${s}"


def calcular_score(risco: str, desconto: float, ocupado: bool) -> float:
    score = 10.0

    if (risco or "").strip().lower() == "alto":
        score -= 3

    if float(desconto or 0) < 20:
        score -= 2

    if ocupado:
        score -= 2

    return max(0.0, round(score, 1))


def recomendacao(score: float, risco: str) -> str:
    r = (risco or "").strip().lower()
    if score >= 8.5 and r != "alto":
        return "Vale a pena com risco controlado"
    if score >= 7.0:
        return "Pode valer a pena, mas confira pontos críticos do edital"
    if r == "alto":
        return "Cuidado: risco alto. Só avance se tiver estratégia jurídica e margem"
    return "Provavelmente não compensa pelo risco/margem"


st.set_page_config(page_title="Leilão Imóveis — decisão em segundos", layout="wide")
st.title("Plataforma de imóveis em leilão")
st.caption("Fluxo: buscar imóvel → colar edital → ver análise → calcular custo real → decisão clara")

if "selected" not in st.session_state:
    st.session_state.selected = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "costs" not in st.session_state:
    st.session_state.costs = None

col_search, col_edital, col_result = st.columns([1.05, 1.35, 1.2], gap="large")

with col_search:
    st.subheader("1) Buscar imóveis")
    cidade = st.text_input("Cidade", value="São Paulo")
    desconto_min = st.slider("Desconto mínimo (%)", min_value=0, max_value=70, value=30, step=5)

    if st.button("Buscar", use_container_width=True):
        st.session_state.selected = None
        st.session_state.analysis = None
        st.session_state.costs = None
        st.session_state.results = search_properties(SearchQuery(cidade=cidade, desconto_min=desconto_min))

    results = st.session_state.get("results", [])
    if results:
        st.write(f"{len(results)} imóvel(is) encontrado(s)")
        options = [f"{p.titulo} — {_fmt_brl(p.preco_leilao)} ({p.desconto:.0f}% off) [{p.fonte}]" for p in results]
        idx = st.radio("Selecione um imóvel", options=options, index=0)
        selected = results[options.index(idx)]
        st.session_state.selected = selected

        st.markdown("**Dados**")
        st.write(
            {
                "titulo": selected.titulo,
                "preco_leilao": selected.preco_leilao,
                "preco_mercado": selected.preco_mercado,
                "desconto": selected.desconto,
                "fonte": selected.fonte,
                "link": selected.link,
            }
        )
    else:
        st.info("Busque para ver imóveis. Se quiser, comece com desconto mínimo 30% em São Paulo.")

with col_edital:
    st.subheader("2) Colar edital e analisar")
    edital_text = st.text_area(
        "Texto do edital",
        height=300,
        placeholder="Cole aqui um trecho do edital (ocupação, dívidas, regras de pagamento...)",
    )
    can_analyze = bool(st.session_state.selected) and bool(edital_text.strip())
    if st.button("Analisar edital", use_container_width=True, disabled=not can_analyze):
        st.session_state.analysis = analyze_edital_text(edital_text)
        st.session_state.costs = None

    analysis = st.session_state.analysis
    if analysis:
        st.markdown("**Resultado estruturado**")
        st.write(
            {
                "ocupado": analysis.ocupado,
                "financiamento": analysis.financiamento,
                "dividas": analysis.dividas,
                "risco": analysis.risco,
                "resumo": analysis.resumo,
            }
        )

with col_result:
    st.subheader("3) Custo real + decisão")
    selected = st.session_state.selected
    analysis = st.session_state.analysis

    if not selected:
        st.info("Selecione um imóvel para ver o custo e score.")
    else:
        ocupado = bool(analysis.ocupado) if analysis else False

        if st.button("Calcular custo real", use_container_width=True, disabled=analysis is None):
            st.session_state.costs = calcular_custos(
                CostInput(preco_leilao=selected.preco_leilao, cidade=cidade, ocupado=ocupado)
            )

        costs = st.session_state.costs
        if analysis and costs:
            score = calcular_score(risco=analysis.risco, desconto=selected.desconto, ocupado=analysis.ocupado)
            rec = recomendacao(score=score, risco=analysis.risco)

            st.metric("Score", f"{score}/10")
            st.write(
                {
                    "preco_leilao": _fmt_brl(selected.preco_leilao),
                    "custo_real_total": _fmt_brl(costs.total),
                    "valor_mercado": _fmt_brl(selected.preco_mercado),
                    "recomendacao": rec,
                }
            )

            st.markdown("**Detalhamento (estimado)**")
            st.write(
                {
                    "itbi": _fmt_brl(costs.itbi),
                    "cartorio": _fmt_brl(costs.cartorio),
                    "advogado": _fmt_brl(costs.advogado),
                    "reforma": _fmt_brl(costs.reforma),
                    "total": _fmt_brl(costs.total),
                    "observacao": costs.observacao,
                }
            )
        elif analysis:
            st.info("Calcule o custo real para fechar a decisão.")
        else:
            st.info("Cole e analise um edital antes de calcular custo.")
