from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchQuery:
    cidade: str
    desconto_min: float


@dataclass(frozen=True)
class PropertyListing:
    titulo: str
    preco_leilao: float
    preco_mercado: float
    desconto: float
    fonte: str
    link: str


def calcular_desconto(preco_mercado: float, preco_leilao: float) -> float:
    if preco_mercado <= 0:
        return 0.0
    return round(((preco_mercado - preco_leilao) / preco_mercado) * 100, 2)


def search_properties(query: SearchQuery) -> list[PropertyListing]:
    seed = [
        PropertyListing(
            titulo="Apartamento Tatuapé",
            preco_leilao=180_000,
            preco_mercado=300_000,
            desconto=calcular_desconto(300_000, 180_000),
            fonte="Caixa",
            link="https://exemplo.com/imovel/1",
        ),
        PropertyListing(
            titulo="Casa Vila Mariana",
            preco_leilao=520_000,
            preco_mercado=780_000,
            desconto=calcular_desconto(780_000, 520_000),
            fonte="Mega Leilões",
            link="https://exemplo.com/imovel/2",
        ),
        PropertyListing(
            titulo="Studio Centro",
            preco_leilao=145_000,
            preco_mercado=210_000,
            desconto=calcular_desconto(210_000, 145_000),
            fonte="Caixa",
            link="https://exemplo.com/imovel/3",
        ),
        PropertyListing(
            titulo="Apartamento Mooca",
            preco_leilao=265_000,
            preco_mercado=410_000,
            desconto=calcular_desconto(410_000, 265_000),
            fonte="Mega Leilões",
            link="https://exemplo.com/imovel/4",
        ),
        PropertyListing(
            titulo="Casa Osasco (Grande SP)",
            preco_leilao=240_000,
            preco_mercado=330_000,
            desconto=calcular_desconto(330_000, 240_000),
            fonte="Caixa",
            link="https://exemplo.com/imovel/5",
        ),
        PropertyListing(
            titulo="Apartamento Santo André (ABC)",
            preco_leilao=230_000,
            preco_mercado=320_000,
            desconto=calcular_desconto(320_000, 230_000),
            fonte="Mega Leilões",
            link="https://exemplo.com/imovel/6",
        ),
        PropertyListing(
            titulo="Terreno Itaquera",
            preco_leilao=120_000,
            preco_mercado=200_000,
            desconto=calcular_desconto(200_000, 120_000),
            fonte="Caixa",
            link="https://exemplo.com/imovel/7",
        ),
        PropertyListing(
            titulo="Cobertura Santana",
            preco_leilao=680_000,
            preco_mercado=980_000,
            desconto=calcular_desconto(980_000, 680_000),
            fonte="Mega Leilões",
            link="https://exemplo.com/imovel/8",
        ),
        PropertyListing(
            titulo="Apartamento Pinheiros",
            preco_leilao=790_000,
            preco_mercado=1_050_000,
            desconto=calcular_desconto(1_050_000, 790_000),
            fonte="Caixa",
            link="https://exemplo.com/imovel/9",
        ),
        PropertyListing(
            titulo="Apartamento Butantã",
            preco_leilao=315_000,
            preco_mercado=450_000,
            desconto=calcular_desconto(450_000, 315_000),
            fonte="Mega Leilões",
            link="https://exemplo.com/imovel/10",
        ),
    ]

    cidade = (query.cidade or "").strip().lower()
    desconto_min = float(query.desconto_min or 0)

    def matches_city(item: PropertyListing) -> bool:
        if not cidade:
            return True
        t = item.titulo.lower()
        if cidade in t:
            return True
        if cidade in {"sao paulo", "são paulo", "sp"}:
            return True
        return False

    results = [p for p in seed if matches_city(p) and p.desconto >= desconto_min]
    results.sort(key=lambda p: (p.desconto, -p.preco_mercado), reverse=True)
    return results
