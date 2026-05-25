"""
Orquestrador principal usando Scrapling StealthySession.

O StealthySession (patchright + flags anti-fingerprint) fornece navegação
resistente a anti-bot genérico. O CAPTCHA da ANP é imagem Oracle APEX e é
tratado pelo módulo captcha.py (ddddocr / manual / 2Captcha).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from scrapling.fetchers import StealthySession

from anp_scraper.automation import AnpPageAutomation
from anp_scraper.config import ScraperConfig
from anp_scraper.exceptions import AnpScraperError, ExportError
from anp_scraper.validators import validate_export_file

log = logging.getLogger(__name__)


@dataclass
class ScrapeResult:
    """Resultado da execução."""

    download_path: str
    validation: dict[str, Any]


class AnpDistributionScraper:
    """Scraper da consulta Base de Distribuição e TRR Autorizados (ANP)."""

    def __init__(self, config: ScraperConfig | None = None) -> None:
        self.config = config or ScraperConfig()
        self._result_box: dict[str, Any] = {}

    def _build_page_action(self):
        automation = AnpPageAutomation(self.config, self._result_box)

        def page_action(page):
            automation.run(page)

        return page_action

    def run(self) -> ScrapeResult:
        """
        Executa o fluxo completo e retorna metadados do arquivo exportado.

        Raises:
            AnpScraperError: falhas de CAPTCHA, exportação ou validação.
        """
        log.info("Iniciando scraper ANP CDP")
        log.info("URL: %s", self.config.url)
        self._result_box.clear()

        session_kwargs = {
            "headless": self.config.headless,
            "timeout": self.config.page_timeout_ms,
            "network_idle": True,
            "load_dom": True,
            "solve_cloudflare": self.config.solve_cloudflare,
            "real_chrome": self.config.real_chrome,
            "google_search": False,
            "disable_resources": False,
            "additional_args": {
                "accept_downloads": True,
                "locale": "pt-BR",
            },
            "page_action": self._build_page_action(),
        }

        try:
            with StealthySession(**session_kwargs) as session:
                log.info("Sessão stealth Scrapling iniciada (patchright)")
                session.fetch(self.config.url)
        except Exception as exc:
            raise AnpScraperError(f"Falha na sessão de navegação: {exc}") from exc

        download_path = self._result_box.get("download_path")
        if not download_path:
            raise ExportError("Exportação não produziu arquivo (download_path ausente).")

        from pathlib import Path

        path = Path(download_path)
        validation = validate_export_file(path)
        return ScrapeResult(download_path=str(path.resolve()), validation=validation)
