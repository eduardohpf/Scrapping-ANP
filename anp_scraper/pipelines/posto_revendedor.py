"""Pipeline br_anp_posto_combustivel_revendedor — Postos revendedores."""
from __future__ import annotations

from anp_scraper.pipelines.spec import PageSelectors, PipelineSpec

CDP_BASE = "https://cdp.anp.gov.br/ords/r/cdp_apex/consulta-dados-publicos-cdp"

HOME_URL = f"{CDP_BASE}/home"

POSTO_TYPE_LABEL = "POSTO REVENDEDOR"
POSTO_TYPE_VALUE = "1"

SELECTORS = PageSelectors(
    primary_filter="#P7_TIPO_POSTO",
    captcha_container="#anp_p7_captcha_1",
    captcha_images="#anp_p7_captcha_1 img",
    captcha_input="#P7_CAPTCHA_1",
    captcha_refresh="#spn_captchaanp_refresh_anp_p7_captcha_1",
    export_button="#B627337254132141370",
    simp_menu_button="#L473316189560854300",
    simp_menu_id="menu_L473316189560854300",
    simp_consulta_link_text="Consulta de Postos",
)

PIPELINE = PipelineSpec(
    name="br_anp_posto_combustivel_revendedor",
    description="Consulta de Postos — Posto Revendedor com tancagem",
    url=HOME_URL,
    selectors=SELECTORS,
    filter_label=POSTO_TYPE_LABEL,
    filter_value=POSTO_TYPE_VALUE,
    navigate_from_home=True,
    export_button_label="Exportar Com Tancagem",
    download_timeout_ms=600_000,
)
