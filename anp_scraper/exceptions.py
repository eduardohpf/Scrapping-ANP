"""Exceções do scraper ANP."""


class AnpScraperError(Exception):
    """Erro base do scraper."""


class CaptchaSolveError(AnpScraperError):
    """Falha ao resolver o CAPTCHA após todas as tentativas."""


class ExportError(AnpScraperError):
    """Falha na exportação ou download do arquivo."""


class ValidationError(AnpScraperError):
    """Arquivo exportado inválido ou vazio."""
