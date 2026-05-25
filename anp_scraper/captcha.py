"""
Resolução do CAPTCHA Oracle APEX (imagem) da ANP.

Estratégia anti-CAPTCHA (em ordem de prioridade):
1. Scrapling StealthySession (patchright): reduz detecção de automação no portal.
   O site NÃO usa Cloudflare Turnstile; solve_cloudflare permanece desligado.
2. OCR local (ddddocr): o plugin ANP exibe 5 imagens (5 caracteres). Concatenamos
   OCR por segmento e, se necessário, OCR da área completa #anp_p25_captcha.
3. Retry: botão de refresh do CAPTCHA + nova leitura até max_captcha_attempts.
4. Modo manual (headless=False): aguarda digitação humana no campo #P25_CAPTCHA.
5. Opcional: API 2Captcha (CAPTCHA_API_KEY) para CAPTCHA de imagem via base64.
"""
from __future__ import annotations

import base64
import logging
import re
from typing import TYPE_CHECKING, Protocol

import ddddocr

if TYPE_CHECKING:
    from patchright.sync_api import Page as SyncPage
    from playwright.async_api import Page as AsyncPage

log = logging.getLogger(__name__)

_ALNUM = re.compile(r"[^a-zA-Z0-9]")


class CaptchaSolver(Protocol):
    def solve(self, page: SyncPage | AsyncPage) -> str: ...


class DdddOcrCaptchaSolver:
    """OCR dedicado para CAPTCHA composto por segmentos."""

    def __init__(self) -> None:
        self._ocr = ddddocr.DdddOcr(show_ad=False)

    @staticmethod
    def _normalize(text: str, length: int = 5) -> str:
        cleaned = _ALNUM.sub("", text or "")
        return cleaned[:length]

    def _classify(self, png: bytes) -> str:
        try:
            return self._normalize(self._ocr.classification(png))
        except Exception as exc:
            log.debug("OCR falhou em um segmento: %s", exc)
            return ""

    def solve_sync(self, page: SyncPage) -> str:
        page.locator("#anp_p25_captcha img").first.wait_for(state="visible", timeout=30_000)
        parts: list[str] = []
        imgs = page.locator("#anp_p25_captcha img")
        for i in range(imgs.count()):
            parts.append(self._classify(imgs.nth(i).screenshot()))

        combined = "".join(parts)
        if len(combined) >= 4:
            log.debug("CAPTCHA OCR (segmentos): %r", combined[:5])
            return combined[:5]

        full = self._classify(page.locator("#anp_p25_captcha").screenshot())
        log.debug("CAPTCHA OCR (área completa): %r", full)
        return full

    async def solve_async(self, page: AsyncPage) -> str:
        await page.locator("#anp_p25_captcha img").first.wait_for(state="visible", timeout=30_000)
        parts: list[str] = []
        imgs = page.locator("#anp_p25_captcha img")
        count = await imgs.count()
        for i in range(count):
            png = await imgs.nth(i).screenshot()
            parts.append(self._classify(png))

        combined = "".join(parts)
        if len(combined) >= 4:
            log.debug("CAPTCHA OCR (segmentos): %r", combined[:5])
            return combined[:5]

        full_png = await page.locator("#anp_p25_captcha").screenshot()
        full = self._classify(full_png)
        log.debug("CAPTCHA OCR (área completa): %r", full)
        return full


class TwoCaptchaSolver:
    """Fallback via API 2Captcha (image captcha). Requer pacote requests e API key."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def _fetch_image_b64(self, page: SyncPage) -> str:
        png = page.locator("#anp_p25_captcha").screenshot()
        return base64.b64encode(png).decode()

    def solve_sync(self, page: SyncPage) -> str:
        import time

        import requests

        b64 = self._fetch_image_b64(page)
        payload = {
            "key": self.api_key,
            "method": "base64",
            "body": b64,
            "regsense": 1,
            "max_len": 5,
        }
        log.info("Enviando CAPTCHA para 2Captcha...")
        create = requests.post("https://2captcha.com/in.php", data=payload, timeout=30)
        create.raise_for_status()
        if not create.text.startswith("OK|"):
            raise RuntimeError(create.text)
        job_id = create.text.split("|", 1)[1]

        for _ in range(24):
            time.sleep(5)
            res = requests.get(
                "https://2captcha.com/res.php",
                params={"key": self.api_key, "action": "get", "id": job_id},
                timeout=30,
            )
            res.raise_for_status()
            if res.text.startswith("OK|"):
                code = res.text.split("|", 1)[1]
                log.info("2Captcha retornou código")
                return DdddOcrCaptchaSolver._normalize(code)
            if res.text != "CAPCHA_NOT_READY":
                raise RuntimeError(res.text)
        raise TimeoutError("2Captcha timeout")


def wait_manual_captcha_sync(page: SyncPage, timeout_ms: int = 300_000) -> str:
    """Aguarda o usuário preencher o CAPTCHA manualmente (modo headful)."""
    log.warning(
        "Modo manual: preencha o CAPTCHA no navegador (timeout %ss)...",
        timeout_ms // 1000,
    )
    page.locator("#P25_CAPTCHA").click()
    page.wait_for_function(
        """() => {
            const el = document.querySelector('#P25_CAPTCHA');
            return el && el.value && el.value.trim().length >= 4;
        }""",
        timeout=timeout_ms,
    )
    return page.locator("#P25_CAPTCHA").input_value().strip()[:5]
