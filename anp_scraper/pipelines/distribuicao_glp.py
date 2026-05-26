"""Pipeline br_anp_distribuicao_glp — Bases do ramo de liquefeitos."""
from __future__ import annotations

from anp_scraper.pipelines.spec import PageSelectors, PipelineSpec

CDP_BASE = "https://cdp.anp.gov.br/ords/r/cdp_apex/consulta-dados-publicos-cdp"

TARGET_URL = f"{CDP_BASE}/base-de-distribuição-e-trr-autorizados-lista"

INSTALLATION_TYPE_LABEL = "BASES DO RAMO DE LIQUEFEITOS"
INSTALLATION_TYPE_VALUE = "3"

SELECTORS = PageSelectors(
    primary_filter="#P25_QUALIFICACAO",
    captcha_container="#anp_p25_captcha",
    captcha_images="#anp_p25_captcha img",
    captcha_input="#P25_CAPTCHA",
    captcha_refresh="#spn_captchaanp_refresh_anp_p25_captcha",
    export_button="#B479395808106517986",
)

PIPELINE = PipelineSpec(
    name="br_anp_distribuicao_glp",
    description="Bases de Distribuição e TRR Autorizados — Liquefeitos",
    url=TARGET_URL,
    selectors=SELECTORS,
    filter_label=INSTALLATION_TYPE_LABEL,
    filter_value=INSTALLATION_TYPE_VALUE,
    navigate_from_home=False,
    export_button_label="Exportar c/ todos os participantes",
)
