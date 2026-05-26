"""Configurações de execução do scraper ANP."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from anp_scraper.pipelines import DEFAULT_PIPELINE, get_pipeline
from anp_scraper.pipelines.distribuicao_glp import (
    INSTALLATION_TYPE_LABEL,
    INSTALLATION_TYPE_VALUE,
    SELECTORS,
    TARGET_URL,
)

# Retrocompatibilidade com imports e documentação existentes
SELECTORS_LEGACY = {
    "installation_type": SELECTORS.primary_filter,
    "captcha_container": SELECTORS.captcha_container,
    "captcha_images": SELECTORS.captcha_images,
    "captcha_input": SELECTORS.captcha_input,
    "captcha_refresh": SELECTORS.captcha_refresh,
    "export_all_participants": SELECTORS.export_button,
    "search_button": "#B430320450206705029",
    "apex_error": SELECTORS.apex_error,
}

DEFAULT_DOWNLOAD_ROOT = Path(__file__).resolve().parent.parent / "output" / "downloads"


@dataclass
class ScraperConfig:
    """Parâmetros de execução do scraper."""

    pipeline: str = DEFAULT_PIPELINE
    url: str | None = None
    installation_label: str = INSTALLATION_TYPE_LABEL
    installation_value: str = INSTALLATION_TYPE_VALUE
    download_dir: Path | None = None
    headless: bool = True
    max_captcha_attempts: int = 8
    page_timeout_ms: int = 120_000
    download_timeout_ms: int = 180_000
    captcha_mode: str = "auto"  # auto | manual | api
    captcha_api_key: str | None = None
    use_scrapling_stealth: bool = True
    solve_cloudflare: bool = False
    real_chrome: bool = False
    log_level: str = "INFO"

    def resolved_download_dir(self) -> Path:
        if self.download_dir is not None:
            return self.download_dir
        # Mantém pasta plana para a pipeline original (compatibilidade)
        if self.pipeline == DEFAULT_PIPELINE:
            return DEFAULT_DOWNLOAD_ROOT
        return DEFAULT_DOWNLOAD_ROOT / self.pipeline

    def resolved_url(self) -> str:
        if self.url is not None:
            return self.url
        return get_pipeline(self.pipeline).url

    @property
    def download_dir_effective(self) -> Path:
        """Diretório efetivo (cria subpasta por pipeline se não customizado)."""
        return self.resolved_download_dir()
