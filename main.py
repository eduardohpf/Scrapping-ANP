#!/usr/bin/env python3
"""
CLI do scraper ANP CDP — múltiplas pipelines.

Exemplos:
  python main.py
  python main.py --pipeline br_anp_posto_combustivel_revendedor
  python main.py --no-headless --captcha-mode manual
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from anp_scraper.config import ScraperConfig
from anp_scraper.pipelines import DEFAULT_PIPELINE, PIPELINES
from anp_scraper.scraper import AnpScraper


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    pipeline_help = ", ".join(sorted(PIPELINES))
    parser = argparse.ArgumentParser(
        description="Exporta dados públicos ANP (CDP) com bypass de CAPTCHA.",
    )
    parser.add_argument(
        "--pipeline",
        choices=tuple(PIPELINES.keys()),
        default=os.environ.get("ANP_PIPELINE", DEFAULT_PIPELINE),
        help=f"Pipeline de extração ({pipeline_help})",
    )
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=None,
        help="Diretório de saída do Excel (padrão: output/downloads/<pipeline>)",
    )
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Executar browser sem interface",
    )
    parser.add_argument(
        "--captcha-mode",
        choices=("auto", "manual", "api"),
        default=os.environ.get("CAPTCHA_MODE", "auto"),
        help="auto=ddddocr | manual=digitação humana | api=2Captcha",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=8,
        help="Tentativas de CAPTCHA antes de falhar",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("LOG_LEVEL", "INFO"),
        help="DEBUG, INFO, WARNING...",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(args.log_level)

    config = ScraperConfig(
        pipeline=args.pipeline,
        download_dir=args.download_dir,
        headless=args.headless,
        captcha_mode=args.captcha_mode,
        captcha_api_key=os.environ.get("CAPTCHA_API_KEY"),
        max_captcha_attempts=args.max_attempts,
    )

    try:
        result = AnpScraper(config).run()
    except Exception as exc:
        logging.getLogger(__name__).error("Scraper falhou: %s", exc)
        return 1

    print("\n=== Exportação concluída ===")
    print(f"Pipeline: {result.pipeline}")
    print(f"Arquivo: {result.download_path}")
    print(f"Validação: {result.validation}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
