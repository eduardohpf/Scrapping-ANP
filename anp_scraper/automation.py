"""
Automação da página Oracle APEX: filtros, CAPTCHA e exportação.

Usa waits explícitos do Playwright/patchright (sem sleep fixo arbitrário),
exceto pequena estabilização após refresh do CAPTCHA.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from anp_scraper.captcha import (
    DdddOcrCaptchaSolver,
    TwoCaptchaSolver,
    wait_manual_captcha_sync,
)
from anp_scraper.config import SELECTORS, ScraperConfig
from anp_scraper.exceptions import CaptchaSolveError, ExportError

log = logging.getLogger(__name__)


class AnpPageAutomation:
    """Fluxo de interação com a página de consulta ANP."""

    def __init__(self, config: ScraperConfig, result_box: dict[str, Any]) -> None:
        self.config = config
        self.result_box = result_box
        self._ocr = DdddOcrCaptchaSolver()
        self._api_solver = (
            TwoCaptchaSolver(config.captcha_api_key)
            if config.captcha_mode == "api" and config.captcha_api_key
            else None
        )

    def run(self, page) -> None:
        """Executado como page_action do Scrapling StealthySession."""
        self._wait_apex_ready(page)
        self._select_installation_type(page)
        self._export_with_captcha_retries(page)

    def _wait_apex_ready(self, page) -> None:
        log.info("Aguardando carregamento da página APEX...")
        page.wait_for_selector(SELECTORS["installation_type"], state="visible", timeout=self.config.page_timeout_ms)
        page.wait_for_selector(SELECTORS["captcha_container"], state="visible", timeout=self.config.page_timeout_ms)
        page.locator(SELECTORS["captcha_images"]).first.wait_for(state="visible", timeout=self.config.page_timeout_ms)
        log.info("Formulário e CAPTCHA carregados.")

    def _select_installation_type(self, page) -> None:
        log.info('Selecionando filtro: "%s"', self.config.installation_label)
        select = page.locator(SELECTORS["installation_type"])
        try:
            select.select_option(label=self.config.installation_label)
        except Exception:
            log.warning("Seleção por label falhou; tentando value=%s", self.config.installation_value)
            select.select_option(value=self.config.installation_value)

        # Confirma valor aplicado no <select> nativo APEX
        page.wait_for_function(
            """([sel, expected]) => {
                const el = document.querySelector(sel);
                return el && el.value === expected;
            }""",
            arg=[SELECTORS["installation_type"], self.config.installation_value],
            timeout=15_000,
        )
        log.info("Filtro Tipo de Instalação aplicado.")

    def _read_captcha_code(self, page) -> str:
        if self.config.captcha_mode == "manual":
            return wait_manual_captcha_sync(page)
        if self._api_solver:
            return self._api_solver.solve_sync(page)
        return self._ocr.solve_sync(page)

    def _refresh_captcha(self, page) -> None:
        log.info("Atualizando imagem do CAPTCHA...")
        page.locator(SELECTORS["captcha_refresh"]).click()
        page.locator(SELECTORS["captcha_images"]).first.wait_for(state="visible", timeout=30_000)
        time.sleep(0.8)

    def _page_has_error(self, page) -> str | None:
        err = page.locator(SELECTORS["apex_error"])
        if err.count() == 0:
            return None
        try:
            text = err.first.inner_text(timeout=2000).strip()
            return text or None
        except Exception:
            return None

    def _export_with_captcha_retries(self, page) -> None:
        self.config.download_dir.mkdir(parents=True, exist_ok=True)

        for attempt in range(1, self.config.max_captcha_attempts + 1):
            log.info("Tentativa %s/%s — resolvendo CAPTCHA", attempt, self.config.max_captcha_attempts)
            code = self._read_captcha_code(page)
            if len(code) != 5:
                log.warning(
                    "OCR retornou código inválido (%r, len=%d); refresh e retry",
                    code,
                    len(code),
                )
                self._refresh_captcha(page)
                continue

            page.locator(SELECTORS["captcha_input"]).fill("")
            page.locator(SELECTORS["captcha_input"]).fill(code)
            log.info("CAPTCHA preenchido (%d caracteres)", len(code))

            try:
                path = self._trigger_export_download(page)
                self.result_box["download_path"] = path
                log.info("Download concluído: %s", path)
                return
            except Exception as exc:
                log.warning("Exportação falhou na tentativa %s: %s", attempt, exc)
                alert = self._page_has_error(page)
                if alert:
                    log.warning("Mensagem APEX: %s", alert[:300])
                self._refresh_captcha(page)

        raise CaptchaSolveError(
            f"Não foi possível exportar após {self.config.max_captcha_attempts} tentativas de CAPTCHA."
        )

    def _trigger_export_download(self, page) -> Path:
        export_btn = page.locator(SELECTORS["export_all_participants"])
        export_btn.wait_for(state="visible", timeout=30_000)

        log.info('Clicando em "Exportar c/ todos os participantes"...')
        with page.expect_download(timeout=self.config.download_timeout_ms) as download_info:
            export_btn.click()

        download = download_info.value
        filename = download.suggested_filename or "exportacao_anp.xlsx"
        dest = self.config.download_dir / filename
        download.save_as(dest)

        if not dest.exists() or dest.stat().st_size == 0:
            raise ExportError(f"Download inválido: {dest}")

        return dest
