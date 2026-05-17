"""Send the AI Signal OS weekly brief as a daily email.

Reads env vars:
  SMTP_USER          Gmail address (sender + recipient default)
  SMTP_APP_PASSWORD  16-char Gmail App Password
  EMAIL_TO           recipient (optional, defaults to SMTP_USER)
  PROJECT_ID         project id to export (optional, defaults to 1)
  BRIEF_PATH         override path to the brief markdown (optional)
"""

from __future__ import annotations

import os
import smtplib
import sys
from datetime import date
from email.message import EmailMessage
from html import escape
from pathlib import Path


def md_to_html(md: str) -> str:
    """Tiny markdown-to-HTML for headings, bold, lists, links. Good enough for the brief."""
    import re

    lines = md.splitlines()
    out: list[str] = []
    in_ul = False

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            close_ul()
            out.append("")
            continue

        h = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if h:
            close_ul()
            level = len(h.group(1))
            text = escape(h.group(2))
            out.append(f"<h{level}>{text}</h{level}>")
            continue

        b = re.match(r"^\s*[-*]\s+(.*)$", stripped)
        if b:
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            item = escape(b.group(1))
            item = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item)
            item = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', item)
            out.append(f"<li>{item}</li>")
            continue

        close_ul()
        para = escape(stripped)
        para = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", para)
        para = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', para)
        out.append(f"<p>{para}</p>")

    close_ul()
    body = "\n".join(out)
    return (
        "<!DOCTYPE html><html><body style=\"font-family:-apple-system,Segoe UI,Roboto,sans-serif;"
        "max-width:720px;margin:0 auto;padding:24px;color:#1f2937;line-height:1.55;\">"
        f"{body}"
        "</body></html>"
    )


def main() -> int:
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_APP_PASSWORD")
    if not smtp_user or not smtp_pass:
        print("ERROR: SMTP_USER and SMTP_APP_PASSWORD must be set", file=sys.stderr)
        return 1

    recipient = os.environ.get("EMAIL_TO") or smtp_user
    project_id = os.environ.get("PROJECT_ID", "1")
    brief_path = os.environ.get(
        "BRIEF_PATH", f"data/exports/project_{project_id}_brief.md"
    )

    path = Path(brief_path)
    if not path.exists():
        print(f"ERROR: brief not found at {path}", file=sys.stderr)
        return 2

    md_content = path.read_text(encoding="utf-8")
    today = date.today().isoformat()

    msg = EmailMessage()
    msg["Subject"] = f"AI News Brief — {today}"
    msg["From"] = smtp_user
    msg["To"] = recipient
    msg.set_content(md_content)
    msg.add_alternative(md_to_html(md_content), subtype="html")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    print(f"Sent brief ({len(md_content)} chars) to {recipient}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
