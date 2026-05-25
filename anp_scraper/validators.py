"""Validação do arquivo exportado."""
from __future__ import annotations

import logging
from pathlib import Path

from openpyxl import load_workbook

from anp_scraper.exceptions import ValidationError

log = logging.getLogger(__name__)

MIN_XLSX_BYTES = 1024


def validate_export_file(path: Path) -> dict:
    """
    Valida que o download foi concluído e contém planilha legível.

    Returns:
        dict com metadados (tamanho, linhas, colunas).
    """
    if not path.exists():
        raise ValidationError(f"Arquivo não encontrado: {path}")

    size = path.stat().st_size
    if size < MIN_XLSX_BYTES:
        raise ValidationError(f"Arquivo muito pequeno ({size} bytes): {path}")

    suffix = path.suffix.lower()
    if suffix not in {".xlsx", ".xls"}:
        raise ValidationError(f"Extensão inesperada {suffix!r} em {path}")

    try:
        wb = load_workbook(path, data_only=True)
        ws = wb.active
        # Alguns exports APEX não populam max_row em read_only; contar linhas reais
        row_count = 0
        col_count = 0
        for row in ws.iter_rows(values_only=True):
            if any(cell is not None and str(cell).strip() != "" for cell in row):
                row_count += 1
                col_count = max(col_count, len(row))
        wb.close()
        rows, cols = row_count, col_count
    except Exception as exc:
        raise ValidationError(f"Não foi possível ler Excel: {path}") from exc

    if rows < 2:
        raise ValidationError(f"Planilha sem dados suficientes (linhas={rows})")

    meta = {"path": str(path), "size_bytes": size, "rows": rows, "columns": cols}
    log.info(
        "Exportação validada: %s (%s bytes, %sx%s)",
        path.name,
        size,
        rows,
        cols,
    )
    return meta
