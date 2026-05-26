"""
Automação br_anp_distribuicao_glp — Bases de Distribuição (P25).

Lógica idêntica à versão monolítica anterior; apenas organizada por pipeline.
"""
from __future__ import annotations

import logging
from typing import Any

from anp_scraper.automation.base import BaseAnpAutomation
from anp_scraper.config import ScraperConfig
from anp_scraper.pipelines.spec import PipelineSpec

log = logging.getLogger(__name__)


class DistribuicaoAutomation(BaseAnpAutomation):
    """Fluxo Base de Distribuição e TRR Autorizados (liquefeitos)."""

    def run(self, page) -> None:
        self._wait_apex_ready(page)
        self._select_primary_filter(page)
        self._export_with_captcha_retries(page)

    def _wait_apex_ready(self, page) -> None:
        log.info("Aguardando carregamento da página APEX...")
        page.wait_for_selector(
            self.selectors.primary_filter,
            state="visible",
            timeout=self.config.page_timeout_ms,
        )
        self._wait_captcha_ready(page)
        log.info("Formulário e CAPTCHA carregados.")


# Alias retrocompatível com código e scripts existentes
AnpPageAutomation = DistribuicaoAutomation


def build_distribuicao_automation(
    config: ScraperConfig,
    spec: PipelineSpec,
    result_box: dict[str, Any],
) -> DistribuicaoAutomation:
    return DistribuicaoAutomation(config, spec, result_box)
