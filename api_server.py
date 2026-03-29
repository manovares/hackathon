from __future__ import annotations

from dataclasses import asdict
import json
import os
import re
from pathlib import Path
from typing import Any

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from cost_calculator import CostInput, calcular_custos
from edital_analyzer import analyze_edital_text
from search_service import SearchQuery, search_properties


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"

app = FastAPI(title="Lance AI", version="0.1.0")


# =========================
# MODELS
# =========================

class SearchRequest(BaseModel):
    cidade: str = "São Paulo"
    desconto_min: float = 30


class AnalyzeRequest(BaseModel):
    texto: str


class CostRequest(BaseModel):
    preco_leilao: float
    cidade: str = "São Paulo"
    ocupado: bool = False


class ScoreRequest(BaseModel):
    risco: str
    desconto: float
    ocupado: bool


# =========================
# BUSINESS LOGIC
# =========================

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


# =========================
# GEMINI
# =========================

def _gemini_api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    key = (key or "").strip()
    return key or None


def _extract_json_object(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None

    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _normalize_risco(value: str | None) -> str:
    v = (value or "").strip().lower()
    if v in {"alto", "baixo", "médio", "medio"}:
        return "médio" if v in {"médio", "medio"} else v
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


def _call_gemini_extract(texto_edital: str) -> dict[str, Any] | None:
    api_key = _gemini_api_key()
    if not api_key:
        return None

    prompt = f"""
Extraia informacoes relevantes de um edital de leilao imobiliario.

Retorne APENAS um JSON valido com:
- ocupado (true/false)
- financiamento (true/false)
- dividas (array de strings)
- risco ("baixo", "medio", "alto")
- resumo (string simples)

Texto:
{texto_edital}
"""

    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 512},
    }

    req = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    try:
        text_out = payload["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None

    return _extract_json_object(text_out)


# =========================
# ROUTES
# =========================

@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    html_path = STATIC_DIR / "index.html"

    if not html_path.exists():
        return HTMLResponse(content="<h1>index.html não encontrado</h1>", status_code=404)

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    return HTMLResponse(content=html)


@app.post("/api/search")
def api_search(body: SearchRequest):
    results = search_properties(
        SearchQuery(cidade=body.cidade, desconto_min=body.desconto_min)
    )
    return [asdict(r) for r in results]


@app.post("/api/analyze")
def api_analyze(body: AnalyzeRequest):
    heuristic = analyze_edital_text(body.texto)
    merged = asdict(heuristic)

    llm = _call_gemini_extract(body.texto)

    if isinstance(llm, dict):
        merged.update(llm)

    merged["risco"] = _apply_business_rules(
        ocupado=bool(merged.get("ocupado")),
        dividas=list(merged.get("dividas") or []),
        risco_base=str(merged.get("risco") or "médio"),
    )

    return merged


@app.post("/api/cost")
def api_cost(body: CostRequest):
    costs = calcular_custos(
        CostInput(
            preco_leilao=body.preco_leilao,
            cidade=body.cidade,
            ocupado=body.ocupado,
        )
    )
    return asdict(costs)


@app.post("/api/score")
def api_score(body: ScoreRequest):
    score = calcular_score(
        risco=body.risco,
        desconto=body.desconto,
        ocupado=body.ocupado,
    )
    rec = recomendacao(score=score, risco=body.risco)
    return {"score": score, "recomendacao": rec}