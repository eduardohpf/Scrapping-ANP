"""Configurações e seletores estáveis da página Oracle APEX."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# URL oficial da consulta pública ANP/CDP
TARGET_URL = (
    "https://cdp.anp.gov.br/ords/r/cdp_apex/"
    "consulta-dados-publicos-cdp/base-de-distribuição-e-trr-autorizados-lista"
)

# Texto exato exibido no dropdown (site usa "BASES", não "BASE")
INSTALLATION_TYPE_LABEL = "BASES DO RAMO DE LIQUEFEITOS"
INSTALLATION_TYPE_VALUE = "3"

# Seletores APEX (IDs estáveis no page item P25)
SELECTORS = {
    "installation_type": "#P25_QUALIFICACAO",
    "captcha_container": "#anp_p25_captcha",
    "captcha_images": "#anp_p25_captcha img",
    "captcha_input": "#P25_CAPTCHA",
    "captcha_refresh": "#spn_captchaanp_refresh_anp_p25_captcha",
    "export_all_participants": "#B479395808106517986",
    "search_button": "#B430320450206705029",
    "apex_error": ".a-Notification-message, .t-Alert-body, .a-Form-error:visible",
}

DEFAULT_DOWNLOAD_DIR = Path(__file__).resolve().parent.parent / "output" / "downloads"


@dataclass
class ScraperConfig:
    """Parâmetros de execução do scraper."""

    url: str = TARGET_URL
    installation_label: str = INSTALLATION_TYPE_LABEL
    installation_value: str = INSTALLATION_TYPE_VALUE
    download_dir: Path = field(default_factory=lambda: DEFAULT_DOWNLOAD_DIR)
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
