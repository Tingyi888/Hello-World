from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from pathlib import Path
from typing import List

import requests


def send_telegram(bot_token: str, chat_id: str, message: str) -> None:
    if not bot_token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    resp = requests.post(url, json={
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
    }, timeout=30)
    resp.raise_for_status()


def send_email(smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str, mail_to: str, subject: str, html_body: str) -> None:
    if not (smtp_host and smtp_user and smtp_password and mail_to):
        return
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = formataddr(('Weekly Digest', smtp_user))
    msg['To'] = mail_to
    part = MIMEText(html_body, 'html', 'utf-8')
    msg.attach(part)
    with smtplib.SMTP(host=smtp_host, port=int(smtp_port)) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [mail_to], msg.as_string())


def read_text(path: Path) -> str:
    try:
        return path.read_text()
    except Exception:
        return ''
