"""Definições de pipeline (seletores, URLs, filtros)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageSelectors:
    """Seletores Oracle APEX de uma consulta pública."""

    primary_filter: str
    captcha_container: str
    captcha_images: str
    captcha_input: str
    captcha_refresh: str
    export_button: str
    apex_error: str = ".a-Notification-message, .t-Alert-body, .a-Form-error:visible"
    simp_menu_button: str | None = None
    simp_menu_id: str | None = None
    simp_consulta_link_text: str | None = None


@dataclass(frozen=True)
class PipelineSpec:
    """Metadados de uma extração ANP (pipeline de dados)."""

    name: str
    description: str
    url: str
    selectors: PageSelectors
    filter_label: str
    filter_value: str
    navigate_from_home: bool = False
    export_button_label: str = "Exportar"
    download_timeout_ms: int = 180_000
