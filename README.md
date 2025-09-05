# 科研周报系统

一个自动化的科研周报系统：每周从 arXiv 等来源检索与你研究方向匹配的新文献，自动摘要与评分，生成 Markdown/HTML 报告，并通过 Telegram/邮件推送。系统完全基于 GitHub Actions 运行，无需本地电脑在线。

## 快速开始

1. Fork 本仓库
2. 在仓库 Settings → Secrets and variables → Actions 添加必要的密钥：
   - `OPENAI_API_KEY`（可选，用于更高质量摘要）
   - `TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`（可选，用于 Telegram 推送）
   - `SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASSWORD`、`MAIL_TO`（可选，用于邮件推送）
3. 修改 `config.example.yaml` 为你的研究方向关键词与订阅配置，并复制为 `config.yaml`（或在 Actions 中通过仓库变量覆盖）。
4. 该系统默认每周一 08:00 UTC 运行一次，你也可以在 Actions 页面手动触发。

## 目录结构

```
.
├── digest/                 # 代码包
│   ├── __init__.py
│   ├── config.py
│   ├── fetch_arxiv.py
│   ├── summarize.py
│   ├── render.py
│   ├── send.py
│   └── main.py
├── requirements.txt
├── config.example.yaml
├── .github/workflows/weekly.yml
└── README.md
```

## 自定义

- 在 `config.yaml` 中设置关键词、时间范围、最大篇数、过滤类别等
- 可扩展更多数据源（如 CrossRef、Semantic Scholar）到 `digest/` 目录
- 摘要模块支持 OpenAI／本地提取式摘要

## 许可

MIT