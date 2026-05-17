"""One-off: convert EMAIL_SETUP.md to EMAIL_SETUP.pdf.

Run from repo root:
    python scripts/generate_setup_pdf.py
"""

from pathlib import Path

from markdown_pdf import MarkdownPdf, Section

CSS = """
body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
       color: #1f2937; line-height: 1.55; font-size: 11pt; }
h1, h2, h3, h4 { font-family: 'Segoe UI', sans-serif; color: #111827; }
h1 { font-size: 22pt; border-bottom: 2px solid #d1d5db; padding-bottom: 6px; }
h2 { font-size: 16pt; margin-top: 24px; }
h3 { font-size: 13pt; margin-top: 18px; }
code { font-family: 'Consolas', 'Courier New', monospace;
       background: #f3f4f6; padding: 1px 4px; border-radius: 3px; font-size: 9.5pt; }
pre { background: #f3f4f6; padding: 10px; border-left: 3px solid #9ca3af;
      overflow-x: auto; font-size: 9.5pt; }
pre code { background: transparent; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10pt; }
th, td { border: 1px solid #d1d5db; padding: 6px 10px; text-align: left;
         vertical-align: top; }
th { background: #f3f4f6; font-weight: 600; }
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
blockquote { border-left: 3px solid #9ca3af; padding-left: 12px; color: #4b5563;
             margin: 10px 0; }
"""


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    md_path = repo_root / "EMAIL_SETUP.md"
    pdf_path = repo_root / "EMAIL_SETUP.pdf"
    md = md_path.read_text(encoding="utf-8")

    pdf = MarkdownPdf(toc_level=2)
    pdf.meta["title"] = "AI News Email Setup"
    pdf.meta["author"] = "AI Signal OS"
    pdf.add_section(Section(md, toc=True), user_css=CSS)
    pdf.save(str(pdf_path))
    print(f"Wrote {pdf_path} ({pdf_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
