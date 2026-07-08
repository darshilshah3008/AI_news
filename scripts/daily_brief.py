#!/usr/bin/env python3
"""Daily Morning Brief (cloud, Claude API).

One email, every morning, with two things Darshil actually uses day to day:
  1. Today's ready-to-post LinkedIn post (LLM-written, weekday-rotated pillar)
     + a navy quote-card poster attached as PNG.
  2. A live AI news digest (Claude API web search over the last ~24h).

This consolidates the two earlier scripts into a single run/email. Nothing is
posted to LinkedIn automatically — you review the email and publish manually.

Recommended home: commit to ONE repo (e.g. AI_news) at:
  scripts/daily_brief.py
and schedule it with the daily-brief.yml workflow.

Required environment variables (GitHub Actions repo secrets):
  ANTHROPIC_API_KEY  - your Anthropic API key (https://console.anthropic.com)
  SMTP_USER          - sending Gmail address, e.g. you@gmail.com
  SMTP_PASS          - a Gmail App Password (16 chars), NOT your login password
  EMAIL_TO           - where to send it, e.g. darshilshah3008@gmail.com
"""

import os
import re
import json
import ssl
import smtplib
import datetime
from email.message import EmailMessage

import anthropic
from PIL import Image, ImageDraw, ImageFont

MODEL = "claude-sonnet-5"

PROFILE = """
Name: Darshil Shah
Role: Embedded Software / Firmware Engineer, with a strong interest in edge AI
and AI developer tooling.
Core expertise: embedded systems; firmware in C/C++; RTOS (esp. FreeRTOS);
CAN bus & J1939 vehicle networking; embedded CI/CD and hardware-in-the-loop
testing; model-based development (MATLAB/Simulink); field reliability;
industrial/automotive/agricultural embedded.
Edge AI interest: on-device inference (NVIDIA Jetson/Orin), TensorRT, ONNX,
quantization.
Builds in public: "Job Search Copilot" (local-first multi-agent Python CLI for
embedded engineers) and "AI Signal OS" (scores AI news against project
constraints).
Goals on LinkedIn: build credibility, attract recruiters, grow his following.
Never fabricate specific metrics or achievements not implied above.
""".strip()

PILLARS = {
    0: "Embedded engineering deep-dive (RTOS/FreeRTOS, CAN/J1939, debugging, field reliability, embedded CI/CD).",
    1: "Edge AI in practice (deploying models on Jetson/Orin, quantization, TensorRT, ONNX, on-device vs cloud).",
    2: "Building in public (lessons from his own projects, why he built them, what he learned).",
    3: "Career/industry perspective for embedded + AI engineers (skills that matter, what recruiters look for).",
    4: "Practical tip / mini-tutorial (a concrete technique other engineers can use immediately).",
    5: "Building in public (lessons from his own projects, why he built them, what he learned).",
    6: "Career/industry perspective for embedded + AI engineers (skills that matter, what recruiters look for).",
}
ACCENTS = {
    0: "#36D1C4", 1: "#F2A03D", 2: "#6C8CFF", 3: "#E8623D",
    4: "#4FC3E8", 5: "#7BD88F", 6: "#C78BFF",
}


# ---------- LinkedIn post ----------------------------------------------------
def generate_post(client, pillar):
    system = ("You are Darshil's expert LinkedIn ghostwriter. Authentic, "
              "practical, no-hype posts grounded ONLY in his real background. "
              "Never invent metrics.\n\n" + PROFILE)
    user = f"""Write ONE LinkedIn post for today. Pillar: {pillar}

Caption rules: strong 1-line hook; 120-220 words; short scannable paragraphs;
teach something concrete; end with an engagement question; 3-5 hashtags on the
last line; humble-confident tone.

Respond with ONLY valid JSON (no fences):
{{"kicker":"SHORT UPPERCASE LABEL","poster_headline":"6-10 word hook","caption":"full post text"}}"""
    msg = client.messages.create(
        model=MODEL, max_tokens=1500, system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = "".join(b.text for b in msg.content if b.type == "text").strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(raw)


# ---------- AI news digest ---------------------------------------------------
def generate_news(client):
    today = datetime.date.today().strftime("%A, %B %d, %Y")
    prompt = f"""Today is {today}. Build a high-signal digest of the most
important AI developments from the LAST 24-48 HOURS. Use web search to find and
verify current items across: major model/product releases; notable research and
benchmarks; new AI developer tools/agents; funding & business moves; policy &
safety. Pick 6-9 recent, verified items ranked by importance.

Return ONLY an HTML fragment (no wrapper, no fences): start with one
<p><strong>Why it matters today:</strong> ...</p>; group items under short <h3>
headers; each item is a <p> with a <strong>headline</strong>, a 1-2 sentence
summary, and an <a href="URL">source</a>. Skimmable in under 3 minutes."""
    msg = client.messages.create(
        model=MODEL, max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
        messages=[{"role": "user", "content": prompt}],
    )
    html = "".join(b.text for b in msg.content if b.type == "text").strip()
    return re.sub(r"^```(?:html)?|```$", "", html.strip(), flags=re.MULTILINE).strip()


# ---------- Poster -----------------------------------------------------------
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def render_poster(headline, kicker, accent_hex, out_path):
    W = H = 1080
    NAVY, WHITE, MUTE = (10, 31, 68), (238, 242, 248), (150, 168, 196)
    accent = hex_to_rgb(accent_hex)
    bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([90, 150, 160, 160], fill=accent)
    d.text((90, 185), kicker.upper(), font=ImageFont.truetype(bold, 30), fill=accent)
    fh = ImageFont.truetype(bold, 78)
    max_w, words, lines, cur = W - 180, headline.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fh) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    y = 300
    for i, ln in enumerate(lines):
        color = accent if (len(lines) > 1 and i >= len(lines) - 2) else WHITE
        d.text((90, y), ln, font=fh, fill=color)
        y += 92
    d.rectangle([90, 922, 98, 994], fill=accent)
    d.text((118, 922), "Darshil Shah", font=ImageFont.truetype(bold, 40), fill=WHITE)
    d.text((118, 972), "Embedded Software Engineer  -  Edge AI",
           font=ImageFont.truetype(reg, 27), fill=MUTE)
    img.save(out_path)
    return out_path


# ---------- Email ------------------------------------------------------------
def send_brief(caption, kicker, news_html, poster_path):
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    to_addr = os.environ["EMAIL_TO"]
    today = datetime.date.today().strftime("%a, %b %d")

    msg = EmailMessage()
    msg["Subject"] = f"Morning Brief - {today}"
    msg["From"] = smtp_user
    msg["To"] = to_addr

    text = (
        f"MORNING BRIEF - {today}\n\n"
        f"1) TODAY'S LINKEDIN POST ({kicker}) - copy the caption below, attach the poster.\n\n"
        f"{caption}\n\n"
        "----------------------------------------\n\n"
        "2) AI NEWS DIGEST\n\n"
        f"{re.sub(r'<[^>]+>', '', news_html)}\n"
    )
    msg.set_content(text)

    caption_html = caption.replace("\n", "<br>")
    html_doc = f"""<div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.55;color:#1a1a1a;max-width:660px">
      <h2 style="margin:0 0 4px">Morning Brief &middot; {today}</h2>
      <div style="background:#0A1F44;color:#EEF2F8;padding:16px 18px;border-radius:12px;margin:14px 0">
        <div style="font-size:12px;letter-spacing:1px;color:#8ea0bc;margin-bottom:6px">TODAY'S LINKEDIN POST &middot; {kicker}</div>
        <div style="white-space:pre-wrap;font-size:15px">{caption_html}</div>
        <div style="font-size:12px;color:#8ea0bc;margin-top:10px">Poster attached as PNG. Copy the text above into LinkedIn, then upload the poster.</div>
      </div>
      <h3 style="margin:22px 0 6px">AI news digest</h3>
      {news_html}
      <hr style="border:none;border-top:1px solid #ddd;margin:20px 0">
      <p style="color:#888;font-size:12px">Generated automatically via the Claude API.</p>
    </div>"""
    msg.add_alternative(html_doc, subtype="html")

    with open(poster_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="image", subtype="png",
                           filename=os.path.basename(poster_path))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
        s.login(smtp_user, smtp_pass)
        s.send_message(msg)


def main():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    weekday = datetime.date.today().weekday()
    pillar, accent = PILLARS[weekday], ACCENTS[weekday]

    post = generate_post(client, pillar)
    kicker = post.get("kicker", "EMBEDDED SYSTEMS")
    headline = post.get("poster_headline") or post["caption"].split("\n")[0]
    caption = post["caption"]

    try:
        news_html = generate_news(client)
    except Exception as e:  # noqa: BLE001
        news_html = f"<p>(AI news digest unavailable today: {e})</p>"

    date_str = datetime.date.today().isoformat()
    poster = render_poster(headline, kicker, accent, f"poster-{date_str}.png")
    send_brief(caption, kicker, news_html, poster)
    print(f"Sent Morning Brief {date_str} | pillar {weekday} | accent {accent}")


if __name__ == "__main__":
    main()
