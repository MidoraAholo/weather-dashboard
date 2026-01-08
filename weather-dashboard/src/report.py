"""Report generation utilities: HTML and PDF exports."""
from __future__ import annotations
from pathlib import Path
from typing import List
import plotly.graph_objects as go

try:
    import pdfkit  # wrapper around wkhtmltopdf
except Exception:  # pragma: no cover
    pdfkit = None


def generate_html_report(figs: List[go.Figure], path: str, title: str = "Report") -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    parts = [f"<h1>{title}</h1>"]
    for i, fig in enumerate(figs):
        parts.append(fig.to_html(full_html=False, include_plotlyjs='cdn'))
    html = "\n".join(parts)
    p.write_text(f"<html><head><meta charset=\"utf-8\"></head><body>{html}</body></html>")


def generate_pdf_report(html_path: str, pdf_path: str) -> None:
    if pdfkit is None:
        raise RuntimeError("pdfkit is not available; install wkhtmltopdf and pdfkit")
    pdfkit.from_file(html_path, pdf_path)
