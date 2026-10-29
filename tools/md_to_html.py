#!/usr/bin/env python3
"""Convierte Markdown a un HTML autocontenido con estilo de informe."""

import sys
from pathlib import Path

import markdown

CSS = """
:root{--ink:#0b1a2d;--muted:#5d7085;--accent:#0f766e;--accent2:#1d4ed8;--line:#d8e1ea;--gold:#b45309;}
*{box-sizing:border-box}
body{font-family:"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);line-height:1.55;font-size:10.5pt;margin:0;background:#fff}
main{max-width:980px;margin:0 auto;padding:32px 28px 60px}
h1{font-size:26pt;line-height:1.1;letter-spacing:-.8px;margin:0 0 6px}
h2{font-size:16pt;letter-spacing:-.3px;margin:26px 0 10px;padding-top:8px;border-top:2px solid var(--accent);page-break-after:avoid}
h3{font-size:12.5pt;margin:18px 0 8px;color:var(--accent);page-break-after:avoid}
p{margin:7px 0}
a{color:var(--accent2);text-decoration:none;word-break:break-word}
strong{color:#0b1a2d}
blockquote{margin:12px 0;padding:10px 14px;border-left:4px solid var(--gold);background:#fffbeb;color:#5b4a1e;border-radius:0 8px 8px 0}
table{width:100%;border-collapse:collapse;margin:10px 0 14px;font-size:9pt;page-break-inside:avoid}
th{background:#0f2238;color:#fff;text-align:left;padding:7px 8px;font-size:8.4pt;letter-spacing:.4px;text-transform:uppercase}
td{border-bottom:1px solid var(--line);padding:6px 8px;vertical-align:top}
tr:nth-child(even) td{background:#f7fafc}
ul,ol{margin:6px 0 10px 20px;padding:0}
li{margin:3px 0}
hr{border:0;border-top:1px solid var(--line);margin:22px 0}
code{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:9pt}
pre{background:#f4f7fa;border:1px solid var(--line);border-radius:8px;padding:12px;overflow:auto}
pre code{background:none;padding:0}
@media print{main{max-width:none;padding:0}body{font-size:10pt}}
"""


def convert(md_path, html_path):
    text = Path(md_path).read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "toc", "sane_lists", "nl2br"])
    title = Path(md_path).stem
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>{title}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{CSS}</style></head><body><main>{body}</main></body></html>"""
    Path(html_path).write_text(html, encoding="utf-8")
    print("HTML:", html_path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: md_to_html.py entrada.md salida.html")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
