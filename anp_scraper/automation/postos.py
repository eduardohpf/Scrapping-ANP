"""
Automação br_anp_posto_combustivel_revendedor — Consulta de Postos (P7).

Navega pelo menu SIMP na home e exporta com tancagem.
"""
from __future__ import annotations

import logging
from typing import Any

from anp_scraper.automation.base import BaseAnpAutomation
from anp_scraper.config import ScraperConfig
from anp_scraper.pipelines.spec import PipelineSpec

log = logging.getLogger(__name__)


class PostosAutomation(BaseAnpAutomation):
    """Fluxo Consulta de Postos — Posto Revendedor."""

    def run(self, page) -> None:
        self._navigate_from_home(page)
        self._wait_apex_ready(page)
        self._select_primary_filter(page)
        self._export_with_captcha_retries(page)

    def _navigate_from_home(self, page) -> None:
        log.info("Aguardando home CDP...")
        page.wait_for_load_state("networkidle", timeout=self.config.page_timeout_ms)

        btn_sel = self.selectors.simp_menu_button
        menu_id = self.selectors.simp_menu_id
        link_text = self.selectors.simp_consulta_link_text
        if not btn_sel or not menu_id or not link_text:
            raise RuntimeError("Pipeline postos requer seletores de navegação SIMP.")

        log.info('Abrindo menu SIMP e selecionando "%s"...', link_text)
        page.locator(btn_sel).click()
        menu = page.locator(f"#{menu_id}")
        menu.wait_for(state="visible", timeout=15_000)

        postos_link = menu.locator("a[href*='consulta-de-postos-lista']")
        if postos_link.count() == 0:
            link = menu.get_by_role("link", name=link_text)
        else:
            link = postos_link.first
        link.wait_for(state="visible", timeout=15_000)
        link.click()

        page.wait_for_selector(
            self.selectors.primary_filter,
            state="visible",
            timeout=self.config.page_timeout_ms,
        )
        log.info("Página de consulta de postos carregada.")

    def _wait_apex_ready(self, page) -> None:
        log.info("Aguardando formulário de consulta de postos...")
        page.wait_for_selector(
            self.selectors.primary_filter,
            state="visible",
            timeout=self.config.page_timeout_ms,
        )
        self._wait_captcha_ready(page)
        log.info("Formulário e CAPTCHA carregados.")


def build_postos_automation(
    config: ScraperConfig,
    spec: PipelineSpec,
    result_box: dict[str, Any],
) -> PostosAutomation:
    return PostosAutomation(config, spec, result_box)
