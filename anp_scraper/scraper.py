"""
Orquestrador principal usando Scrapling StealthySession.

Suporta múltiplas pipelines ANP via registro em anp_scraper.pipelines.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from scrapling.fetchers import StealthySession

from anp_scraper.automation.distribuicao import DistribuicaoAutomation
from anp_scraper.automation.postos import PostosAutomation
from anp_scraper.config import ScraperConfig
from anp_scraper.exceptions import AnpScraperError, ExportError
from anp_scraper.pipelines import get_pipeline
from anp_scraper.pipelines.spec import PipelineSpec
from anp_scraper.validators import validate_export_file

log = logging.getLogger(__name__)

_AUTOMATIONS: dict[str, type] = {
    "br_anp_distribuicao_glp": DistribuicaoAutomation,
    "br_anp_posto_combustivel_revendedor": PostosAutomation,
}


@dataclass
class ScrapeResult:
    """Resultado da execução."""

    pipeline: str
    download_path: str
    validation: dict[str, Any]


class AnpScraper:
    """Scraper genérico ANP CDP — seleciona automação pela pipeline."""

    def __init__(
        self,
        config: ScraperConfig | None = None,
        pipeline: str | None = None,
    ) -> None:
        self.config = config or ScraperConfig()
        if pipeline:
            self.config.pipeline = pipeline
        self.spec: PipelineSpec = get_pipeline(self.config.pipeline)
        self._result_box: dict[str, Any] = {}

    def _automation_factory(self) -> Callable:
        cls = _AUTOMATIONS.get(self.spec.name)
        if cls is None:
            raise AnpScraperError(f"Automação não implementada para {self.spec.name!r}")
        return cls

    def _build_page_action(self):
        automation_cls = self._automation_factory()
        config = self._effective_config()
        automation = automation_cls(config, self.spec, self._result_box)

        def page_action(page):
            automation.run(page)

        return page_action

    def _effective_config(self) -> ScraperConfig:
        """Config com URL e download_dir resolvidos para a pipeline."""
        cfg = self.config
        cfg.download_dir = cfg.resolved_download_dir()
        cfg.url = cfg.resolved_url()
        if cfg.download_timeout_ms == 180_000 and self.spec.download_timeout_ms != 180_000:
            cfg.download_timeout_ms = self.spec.download_timeout_ms
        return cfg

    def run(self) -> ScrapeResult:
        """
        Executa o fluxo completo e retorna metadados do arquivo exportado.

        Raises:
            AnpScraperError: falhas de CAPTCHA, exportação ou validação.
        """
        cfg = self._effective_config()
        log.info("Iniciando scraper ANP CDP — pipeline=%s", self.spec.name)
        log.info("URL: %s", cfg.url)
        self._result_box.clear()

        session_kwargs = {
            "headless": cfg.headless,
            "timeout": cfg.page_timeout_ms,
            "network_idle": True,
            "load_dom": True,
            "solve_cloudflare": cfg.solve_cloudflare,
            "real_chrome": cfg.real_chrome,
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
                session.fetch(cfg.url)
        except Exception as exc:
            raise AnpScraperError(f"Falha na sessão de navegação: {exc}") from exc

        download_path = self._result_box.get("download_path")
        if not download_path:
            raise ExportError("Exportação não produziu arquivo (download_path ausente).")

        path = Path(download_path)
        validation = validate_export_file(path)
        return ScrapeResult(
            pipeline=self.spec.name,
            download_path=str(path.resolve()),
            validation=validation,
        )


class AnpDistributionScraper(AnpScraper):
    """Retrocompatível: pipeline br_anp_distribuicao_glp."""

    def __init__(self, config: ScraperConfig | None = None) -> None:
        cfg = config or ScraperConfig()
        super().__init__(cfg, pipeline="br_anp_distribuicao_glp")
