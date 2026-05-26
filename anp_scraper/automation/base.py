"""
Fluxo compartilhado: CAPTCHA, retry e exportação Excel.

Cada pipeline implementa apenas navegação e filtros específicos.
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
from anp_scraper.config import ScraperConfig
from anp_scraper.exceptions import CaptchaSolveError, ExportError
from anp_scraper.pipelines.spec import PageSelectors, PipelineSpec

log = logging.getLogger(__name__)


class BaseAnpAutomation:
    """CAPTCHA + exportação reutilizáveis entre pipelines ANP."""

    def __init__(
        self,
        config: ScraperConfig,
        spec: PipelineSpec,
        result_box: dict[str, Any],
    ) -> None:
        self.config = config
        self.spec = spec
        self.selectors: PageSelectors = spec.selectors
        self.result_box = result_box
        self._ocr = DdddOcrCaptchaSolver()
        self._api_solver = (
            TwoCaptchaSolver(config.captcha_api_key, self.selectors)
            if config.captcha_mode == "api" and config.captcha_api_key
            else None
        )

    def _wait_captcha_ready(self, page) -> None:
        page.wait_for_selector(
            self.selectors.captcha_container,
            state="visible",
            timeout=self.config.page_timeout_ms,
        )
        page.locator(self.selectors.captcha_images).first.wait_for(
            state="visible",
            timeout=self.config.page_timeout_ms,
        )

    def _read_captcha_code(self, page) -> str:
        if self.config.captcha_mode == "manual":
            return wait_manual_captcha_sync(page, self.selectors)
        if self._api_solver:
            return self._api_solver.solve_sync(page)
        return self._ocr.solve_sync(page, self.selectors)

    def _refresh_captcha(self, page) -> None:
        log.info("Atualizando imagem do CAPTCHA...")
        page.locator(self.selectors.captcha_refresh).click()
        page.locator(self.selectors.captcha_images).first.wait_for(state="visible", timeout=30_000)
        time.sleep(0.8)

    def _page_has_error(self, page) -> str | None:
        err = page.locator(self.selectors.apex_error)
        if err.count() == 0:
            return None
        try:
            text = err.first.inner_text(timeout=2000).strip()
            return text or None
        except Exception:
            return None

    def _select_primary_filter(self, page) -> None:
        log.info('Selecionando filtro: "%s"', self.spec.filter_label)
        select = page.locator(self.selectors.primary_filter)
        try:
            select.select_option(label=self.spec.filter_label)
        except Exception:
            log.warning(
                "Seleção por label falhou; tentando value=%s",
                self.spec.filter_value,
            )
            select.select_option(value=self.spec.filter_value)

        page.wait_for_function(
            """([sel, expected]) => {
                const el = document.querySelector(sel);
                return el && el.value === expected;
            }""",
            arg=[self.selectors.primary_filter, self.spec.filter_value],
            timeout=15_000,
        )
        log.info("Filtro principal aplicado.")

    def _export_with_captcha_retries(self, page) -> None:
        self.config.download_dir.mkdir(parents=True, exist_ok=True)

        for attempt in range(1, self.config.max_captcha_attempts + 1):
            log.info(
                "Tentativa %s/%s — resolvendo CAPTCHA",
                attempt,
                self.config.max_captcha_attempts,
            )
            code = self._read_captcha_code(page)
            if len(code) != 5:
                log.warning(
                    "OCR retornou código inválido (%r, len=%d); refresh e retry",
                    code,
                    len(code),
                )
                self._refresh_captcha(page)
                continue

            page.locator(self.selectors.captcha_input).fill("")
            page.locator(self.selectors.captcha_input).fill(code)
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
        export_btn = page.locator(self.selectors.export_button)
        export_btn.wait_for(state="visible", timeout=30_000)

        log.info('Clicando em "%s"...', self.spec.export_button_label)
        export_btn.click()
        download = page.wait_for_event(
            "download",
            timeout=self.config.download_timeout_ms,
        )
        filename = download.suggested_filename or f"exportacao_{self.spec.name}.xlsx"
        dest = self.config.download_dir / filename
        download.save_as(dest)

        if not dest.exists() or dest.stat().st_size == 0:
            raise ExportError(f"Download inválido: {dest}")

        return dest
