from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostInput:
    preco_leilao: float
    cidade: str
    ocupado: bool


@dataclass(frozen=True)
class CostBreakdown:
    itbi: float
    cartorio: float
    advogado: float
    reforma: float
    total: float
    observacao: str


def calcular_custos(input_data: CostInput) -> CostBreakdown:
    preco = float(input_data.preco_leilao or 0)

    itbi = round(preco * 0.03, 2)

    cidade = (input_data.cidade or "").strip().lower()
    if cidade in {"sao paulo", "são paulo", "sp"}:
        cartorio = 3000.0
    else:
        cartorio = 2500.0

    advogado = 10_000.0 if input_data.ocupado else 2_000.0
    reforma = round(preco * 0.10, 2)

    total = round(itbi + cartorio + advogado + reforma + preco, 2)

    return CostBreakdown(
        itbi=itbi,
        cartorio=cartorio,
        advogado=advogado,
        reforma=reforma,
        total=total,
        observacao="Esse valor e estimado.",
    )
