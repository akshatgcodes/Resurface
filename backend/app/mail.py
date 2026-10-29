import html
import smtplib
from email.message import EmailMessage

from app.config import settings

# Inline styles: most mail clients ignore <style> blocks
CARD = "margin:0 0 20px;padding:14px 16px;border-left:3px solid #c2410c;background:#fdf8f3"
QUOTE = "margin:0 0 8px;font:17px/1.5 Georgia,serif;color:#1c1917"
SOURCE = "margin:0;font:13px sans-serif;color:#78716c"
WHY = "margin:4px 0 0;font:12px sans-serif;color:#a8a29e"


def _source_line(p: dict) -> str:
    author = p["source"].get("author")
    return p["source"]["title"] + (f" — {author}" if author else "")


def render(picks: list[dict], public_url: str) -> tuple[str, str, str]:
    """(subject, text, html) for a digest. `picks` are serialized highlights + reason."""
    n = len(picks)
    subject = f"Resurface: {n} highlight{'s' if n != 1 else ''} worth rereading"
    esc = html.escape
    text = "\n\n".join(f"“{p['text']}”\n  {_source_line(p)}\n  ({p['reason']})" for p in picks)
    text += f"\n\nOpen your library: {public_url}\n"
    cards = "".join(
        f'<div style="{CARD}"><p style="{QUOTE}">{esc(p["text"])}</p>'
        f'<p style="{SOURCE}">{esc(_source_line(p))}</p>'
        f'<p style="{WHY}">{esc(p["reason"])}</p></div>'
        for p in picks
    )
    body = (
        '<div style="max-width:560px;margin:0 auto;padding:24px">'
        '<h1 style="font:600 20px sans-serif;color:#1c1917">Today\'s highlights</h1>'
        f"{cards}"
        f'<p style="font:13px sans-serif"><a href="{esc(public_url)}">Open your library</a></p>'
        "</div>"
    )
    return subject, text, body


def send(to: str, subject: str, text: str, body_html: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.mail_from
    msg["To"] = to
    msg.set_content(text)
    msg.add_alternative(body_html, subtype="html")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
