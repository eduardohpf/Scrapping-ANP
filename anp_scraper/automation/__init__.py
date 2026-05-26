"""Automações por pipeline ANP."""
from anp_scraper.automation.base import BaseAnpAutomation
from anp_scraper.automation.distribuicao import AnpPageAutomation, DistribuicaoAutomation
from anp_scraper.automation.postos import PostosAutomation

__all__ = [
    "AnpPageAutomation",
    "BaseAnpAutomation",
    "DistribuicaoAutomation",
    "PostosAutomation",
]
