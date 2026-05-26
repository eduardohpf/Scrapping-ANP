"""Registro de pipelines ANP suportadas."""
from __future__ import annotations

from anp_scraper.pipelines.distribuicao_glp import PIPELINE as DISTRIBUICAO_GLP
from anp_scraper.pipelines.posto_revendedor import PIPELINE as POSTO_REVENDEDOR
from anp_scraper.pipelines.spec import PageSelectors, PipelineSpec

PIPELINES: dict[str, PipelineSpec] = {
    DISTRIBUICAO_GLP.name: DISTRIBUICAO_GLP,
    POSTO_REVENDEDOR.name: POSTO_REVENDEDOR,
}

DEFAULT_PIPELINE = DISTRIBUICAO_GLP.name


def get_pipeline(name: str) -> PipelineSpec:
    """Retorna spec da pipeline pelo nome."""
    key = name.strip()
    if key not in PIPELINES:
        known = ", ".join(sorted(PIPELINES))
        raise KeyError(f"Pipeline desconhecida: {name!r}. Disponíveis: {known}")
    return PIPELINES[key]


__all__ = [
    "DEFAULT_PIPELINE",
    "DISTRIBUICAO_GLP",
    "POSTO_REVENDEDOR",
    "PIPELINES",
    "PageSelectors",
    "PipelineSpec",
    "get_pipeline",
]
