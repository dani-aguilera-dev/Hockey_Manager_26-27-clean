#!/usr/bin/env python3
"""Convierte Markdown a PDF con un estilo limpio para los informes del proyecto."""

import re
import sys
from pathlib import Path

import markdown
from weasyprint import HTML

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm;
  @bottom-center { content: counter(page) " / " counter(pages); font-size: 8pt; color: #666; }
}
* { box-sizing: border-box; }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 10.2pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 20pt; color: #0f3b5c; border-bottom: 2px solid #1f7a5a; padding-bottom: 6px; margin-top: 0; }
h2 { font-size: 14.5pt; color: #0f3b5c; margin-top: 18px; border-bottom: 1px solid #d0d7de; padding-bottom: 3px; page-break-after: avoid; }
h3 { font-size: 12pt; color: #145a7a; margin-top: 14px; page-break-after: avoid; }
h4 { font-size: 10.8pt; color: #145a7a; margin-top: 10px; page-break-after: avoid; }
p { margin: 4px 0 7px; }
ul, ol { margin: 4px 0 8px 18px; padding: 0; }
li { margin: 2px 0; }
a { color: #0b6bcb; text-decoration: none; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 8.8pt; background: #f2f4f7; padding: 1px 3px; border-radius: 3px; }
pre { background: #f2f4f7; border: 1px solid #d0d7de; border-radius: 5px; padding: 8px; font-size: 8.6pt; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 12px; font-size: 8.6pt; page-break-inside: auto; }
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
th { background: #0f3b5c; color: white; text-align: left; padding: 5px 6px; border: 1px solid #0f3b5c; }
td { padding: 4px 6px; border: 1px solid #cfd8e3; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f7f9fc; }
blockquote { margin: 8px 0; padding: 7px 10px; border-left: 3px solid #1f7a5a; background: #f0f8f5; color: #244; }
hr { border: none; border-top: 1px solid #d0d7de; margin: 14px 0; }
strong { color: #0d2f49; }
h1 + p, h1 + blockquote { margin-top: 8px; }
.page-break { page-break-before: always; }
"""


def convert(md_path, pdf_path):
    text = Path(md_path).read_text(encoding="utf-8")
    html_body = markdown.markdown(text, extensions=["tables", "fenced_code", "toc", "sane_lists", "nl2br"])
    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>{Path(md_path).stem}</title>
<style>{CSS}</style></head><body>{html_body}</body></html>"""
    HTML(string=html, base_url=str(Path(md_path).resolve().parent)).write_pdf(str(pdf_path))
    print("PDF:", pdf_path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: md_to_pdf.py entrada.md salida.pdf")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
