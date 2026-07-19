#!/usr/bin/env python3
"""
Convert markdown to PDF with proper formatting
"""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path

# Read markdown file
md_file = Path("/Users/kartikvadhawana/Desktop/FRA/NEWFINALFRA/FRA_Semester_Report_Fall_2025.md")
pdf_file = Path("/Users/kartikvadhawana/Desktop/FRA/NEWFINALFRA/FRA_Semester_Report_Fall_2025.pdf")

print(f"Reading markdown from: {md_file}")
with open(md_file, 'r', encoding='utf-8') as f:
    md_content = f.read()

print("Converting markdown to HTML...")
# Convert markdown to HTML with extensions
html_content = markdown.markdown(
    md_content,
    extensions=[
        'tables',
        'fenced_code',
        'codehilite',
        'nl2br',
        'sane_lists'
    ]
)

# Add CSS styling for professional look
css_style = """
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-size: 10pt;
    line-height: 1.4;
    color: #333;
}

h1 {
    color: #2c3e50;
    font-size: 24pt;
    margin-top: 20pt;
    margin-bottom: 10pt;
    border-bottom: 2px solid #3498db;
    padding-bottom: 5pt;
}

h2 {
    color: #34495e;
    font-size: 18pt;
    margin-top: 15pt;
    margin-bottom: 8pt;
    border-bottom: 1px solid #bdc3c7;
    padding-bottom: 3pt;
}

h3 {
    color: #34495e;
    font-size: 14pt;
    margin-top: 12pt;
    margin-bottom: 6pt;
}

h4 {
    color: #555;
    font-size: 12pt;
    margin-top: 10pt;
    margin-bottom: 5pt;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 10pt 0;
    font-size: 9pt;
}

th {
    background-color: #3498db;
    color: white;
    padding: 6pt;
    text-align: left;
    border: 1px solid #2980b9;
}

td {
    padding: 5pt;
    border: 1px solid #ddd;
}

tr:nth-child(even) {
    background-color: #f8f9fa;
}

code {
    background-color: #f4f4f4;
    padding: 2pt 4pt;
    border-radius: 3pt;
    font-family: 'Courier New', monospace;
    font-size: 9pt;
    color: #c7254e;
}

pre {
    background-color: #2c3e50;
    color: #ecf0f1;
    padding: 10pt;
    border-radius: 5pt;
    overflow-x: auto;
    font-size: 8pt;
    line-height: 1.3;
}

pre code {
    background-color: transparent;
    color: #ecf0f1;
    padding: 0;
}

blockquote {
    border-left: 4px solid #3498db;
    padding-left: 10pt;
    margin-left: 0;
    color: #555;
    font-style: italic;
}

ul, ol {
    margin: 8pt 0;
    padding-left: 20pt;
}

li {
    margin: 3pt 0;
}

strong {
    color: #2c3e50;
}

a {
    color: #3498db;
    text-decoration: none;
}

hr {
    border: none;
    border-top: 1px solid #bdc3c7;
    margin: 15pt 0;
}

.page-break {
    page-break-after: always;
}
"""

# Wrap HTML with proper structure
full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FRA Semester Report Fall 2025</title>
    <style>
        {css_style}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""

print("Generating PDF...")
# Convert HTML to PDF
HTML(string=full_html).write_pdf(pdf_file)

print(f"✓ PDF created successfully: {pdf_file}")
print(f"File size: {pdf_file.stat().st_size / 1024 / 1024:.2f} MB")
