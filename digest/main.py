from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .config import AppConfig, ArxivConfig
from .fetch_arxiv import fetch_arxiv_recent, filter_papers
from .summarize import summarize_and_score_locally, summarize_and_score_llm
from .render import render_reports
from .send import send_telegram, send_email, read_text


def run(config_path: str) -> None:
    cfg = AppConfig.from_yaml(config_path)
    arxiv_cfg: ArxivConfig = cfg.sources['arxiv']

    items: List[str] = []

    if arxiv_cfg.enable:
        papers = fetch_arxiv_recent(
            keywords=arxiv_cfg.keywords,
            categories=arxiv_cfg.categories,
            window_days=arxiv_cfg.window_days,
            max_results=arxiv_cfg.max_results,
        )
        papers = filter_papers(papers, arxiv_cfg.include_regex, arxiv_cfg.exclude_regex)

        # de-duplicate by arXiv id
        unique = {}
        for p in papers:
            unique.setdefault(p.id, p)
        papers = list(unique.values())

        scored = []
        for p in papers:
            if cfg.scoring.use_llm:
                s = summarize_and_score_llm(p.title, p.summary, arxiv_cfg.keywords, cfg.scoring.llm_model, cfg.scoring.max_tokens, cfg.scoring.temperature)
            else:
                s = summarize_and_score_locally(p.title, p.summary, arxiv_cfg.keywords)
            scored.append((s.relevance, s.bullet, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_k = cfg.scoring.top_k
        min_rel = cfg.scoring.min_relevance
        for rel, bullet, p in scored:
            if len(items) >= top_k:
                break
            if rel < min_rel:
                continue
            # add links if available
            link = p.link_abs or p.link_pdf or ''
            if link:
                bullet = bullet + f" [链接]({link})"
            items.append(bullet)

    outputs = render_reports(cfg.title, items, cfg.render.output_dir, cfg.render.formats)

    # delivery
    tg = cfg.deliver.telegram
    if tg.enable:
        import os
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or ((tg.bot_token or '') if not (tg.bot_token or '').startswith('${') else '')
        chat_id = os.getenv('TELEGRAM_CHAT_ID') or ((tg.chat_id or '') if not (tg.chat_id or '').startswith('${') else '')
        preview = '\n'.join(items[:10]) if items else '本周没有匹配到论文。'
        if bot_token and chat_id:
            send_telegram(bot_token, chat_id, f"<b>{cfg.title}</b>\n\n" + preview)

    em = cfg.deliver.email
    if em.enable:
        import os
        smtp_host = os.getenv('SMTP_HOST') or ((em.smtp_host or '') if not (em.smtp_host or '').startswith('${') else '')
        smtp_port_str = os.getenv('SMTP_PORT') or str(em.smtp_port)
        try:
            smtp_port = int(smtp_port_str)
        except Exception:
            smtp_port = em.smtp_port
        smtp_user = os.getenv('SMTP_USER') or ((em.smtp_user or '') if not (em.smtp_user or '').startswith('${') else '')
        smtp_password = os.getenv('SMTP_PASSWORD') or ((em.smtp_password or '') if not (em.smtp_password or '').startswith('${') else '')
        mail_to = os.getenv('MAIL_TO') or ((em.mail_to or '') if not (em.mail_to or '').startswith('${') else '')
        html_path = next((p for p in outputs if p.suffix == '.html'), None)
        html_body = read_text(html_path) if html_path else '<p>无正文</p>'
        if smtp_host and smtp_user and smtp_password and mail_to:
            send_email(
                smtp_host,
                smtp_port,
                smtp_user,
                smtp_password,
                mail_to,
                subject=cfg.title,
                html_body=html_body,
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='config.yaml')
    args = parser.parse_args()
    run(args.config)


if __name__ == '__main__':
    main()

