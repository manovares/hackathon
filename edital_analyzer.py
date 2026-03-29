from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class EditalAnalysis:
    ocupado: bool
    financiamento: bool
    dividas: list[str]
    risco: str
    resumo: str


_DEBT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("IPTU", re.compile(r"\biptu\b", re.IGNORECASE)),
    ("Condomínio", re.compile(r"\bcondom[íi]nio\b|\bcondominial\b", re.IGNORECASE)),
    ("Água", re.compile(r"\b(água|agua)\b", re.IGNORECASE)),
    ("Luz", re.compile(r"\b(luz|energia( elétrica)?)\b", re.IGNORECASE)),
    ("Multas", re.compile(r"\bmulta(s)?\b", re.IGNORECASE)),
    ("Taxas", re.compile(r"\btaxa(s)?\b", re.IGNORECASE)),
]


def _infer_ocupado(texto: str) -> bool:
    t = texto.lower()
    positives = [
        "ocupado",
        "ocupada",
        "ocupação",
        "ocupacao",
        "posse",
        "possuidor",
        "invas",
        "locat",
        "inquilin",
        "terceiros",
    ]
    negatives = [
        "desocupado",
        "desocupada",
        "livre de pessoas",
        "livre e desembaraçado",
        "livre e desembaracado",
        "imissão na posse imediata",
        "imissao na posse imediata",
    ]
    if any(n in t for n in negatives):
        return False
    return any(p in t for p in positives)


def _infer_financiamento(texto: str) -> bool:
    t = texto.lower()
    if "não aceita financiamento" in t or "nao aceita financiamento" in t:
        return False
    if "não permite financiamento" in t or "nao permite financiamento" in t:
        return False
    if "financiamento" in t and ("aceita" in t or "permit" in t):
        return True
    return False


def _extract_dividas(texto: str) -> list[str]:
    found: list[str] = []
    for label, pattern in _DEBT_PATTERNS:
        if pattern.search(texto):
            found.append(label)
    return found


def _normalize_risco(risco: str) -> str:
    r = (risco or "").strip().lower()
    if r in {"alto", "medio", "médio", "baixo"}:
        return "médio" if r in {"medio", "médio"} else r
    return "médio"


def _apply_business_rules(ocupado: bool, dividas: list[str], risco_base: str) -> str:
    r = _normalize_risco(risco_base)

    if ocupado:
        return "alto"

    if dividas:
        if r == "baixo":
            return "médio"
        return "alto"

    return r


def analyze_edital_text(texto: str) -> EditalAnalysis:
    raw = (texto or "").strip()
    ocupado = _infer_ocupado(raw)
    financiamento = _infer_financiamento(raw)
    dividas = _extract_dividas(raw)

    risco_base = "baixo"
    if re.search(r"\bleil[aã]o judicial\b|\bexecu[cç][aã]o\b|\bpenhora\b", raw, re.IGNORECASE):
        risco_base = "médio"
    if re.search(r"\bônus\b|\bonus\b|\bgravame\b|\bhipoteca\b|\baliena[cç][aã]o fiduci[aá]ria\b", raw, re.IGNORECASE):
        risco_base = "médio"

    risco = _apply_business_rules(ocupado=ocupado, dividas=dividas, risco_base=risco_base)

    if ocupado and dividas:
        resumo = "Imovel ocupado com debitos. Pode exigir acao judicial e negociacao de passivos."
    elif ocupado:
        resumo = "Imovel ocupado. Pode exigir acao judicial para imissao na posse."
    elif dividas:
        resumo = "Imovel com debitos informados no edital. Verifique responsabilidade por quitacao e valores."
    else:
        resumo = "Edital sem sinais claros de ocupacao ou debitos no texto colado. Ainda assim, confirme matricula e condicoes."

    return EditalAnalysis(
        ocupado=ocupado,
        financiamento=financiamento,
        dividas=dividas,
        risco=risco,
        resumo=resumo,
    )
