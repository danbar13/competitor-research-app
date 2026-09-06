"""
Module for exporting Markdown reports to styled RTL PDF files using Microsoft Edge.
"""
import os
import subprocess
from pathlib import Path
import markdown
from .settings import RESEARCH_DIR

def find_edge_path() -> str:
    """Locate Microsoft Edge executable on Windows."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return ""

def markdown_to_html(md_text: str, title: str = "דוח מחקר מתחרים") -> str:
    """Convert Markdown text to HTML wrapped in RTL styles."""
    html_body = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'nl2br'])
    
    html_content = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 40px;
            color: #2c3e50;
            line-height: 1.6;
        }}
        h1, h2, h3 {{
            color: #0f4c61;
            border-bottom: 2px solid #e5e5e5;
            padding-bottom: 8px;
        }}
        h1 {{
            font-size: 26px;
            margin-bottom: 20px;
        }}
        h2 {{
            font-size: 20px;
            margin-top: 30px;
        }}
        h3 {{
            font-size: 16px;
            margin-top: 20px;
            border-bottom: none;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
            text-align: right;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
        }}
        th {{
            background-color: #f7f9fa;
            color: #0f4c61;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #fdfdfd;
        }}
        ul, ol {{
            padding-right: 20px;
            padding-left: 0;
        }}
        li {{
            margin-bottom: 8px;
        }}
        strong {{
            color: #111;
        }}
        hr {{
            border: 0;
            border-top: 1px solid #eee;
            margin: 30px 0;
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""
    return html_content

def export_report_to_pdf(md_text: str, filename_base: str, title: str = "דוח מחקר מתחרים") -> Path:
    """
    Save Markdown report and convert it to a styled PDF.
    Returns path to the generated PDF.
    """
    safe_filename = "".join(c for c in filename_base if c.isalnum() or c in ("-", "_", " ")).rstrip()
    if not safe_filename:
        safe_filename = "competitor_report"
        
    md_path = RESEARCH_DIR / f"{safe_filename}.md"
    html_path = RESEARCH_DIR / f"{safe_filename}_temp.html"
    pdf_path = RESEARCH_DIR / f"{safe_filename}.pdf"
    
    # Write Markdown file
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
        
    # Write styled HTML
    html_content = markdown_to_html(md_text, title=title)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    edge_executable = find_edge_path()
    if not edge_executable:
        # If Edge is not found, keep HTML and MD
        return md_path
        
    cmd = [
        edge_executable,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={pdf_path}",
        str(html_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, timeout=30)
        # Clean up temporary HTML
        if html_path.exists():
            html_path.unlink()
        return pdf_path
    except Exception as e:
        print(f"Warning: Failed to generate PDF via Edge: {e}")
        return md_path
