from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

from jinja2 import Template


MD_TEMPLATE = Template(
    """
## {{ title }}

生成时间：{{ generated_at }}

### 精选论文（{{ items|length }} 篇）

{% for it in items %}
{{ it }}
{% endfor %}

---
由自动化周报系统生成。
    """.strip()
)


HTML_TEMPLATE = Template(
    """
<html>
  <head>
    <meta charset="utf-8" />
    <title>{{ title }}</title>
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji"; line-height: 1.6; padding: 2rem; }
      h2, h3 { margin-top: 1.2rem; }
      li { margin: 0.5rem 0; }
      .footer { color: #777; margin-top: 2rem; font-size: 0.9rem; }
    </style>
  </head>
  <body>
    <h2>{{ title }}</h2>
    <p>生成时间：{{ generated_at }}</p>
    <h3>精选论文（{{ items|length }} 篇）</h3>
    <ul>
    {% for it in items %}
      <li>{{ it[2:] }}</li>
    {% endfor %}
    </ul>
    <div class="footer">由自动化周报系统生成。</div>
  </body>
</html>
    """.strip()
)


def render_reports(title: str, items: List[str], output_dir: str, formats: List[str]) -> List[Path]:
    generated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []

    if 'md' in formats:
        md = MD_TEMPLATE.render(title=title, items=items, generated_at=generated_at)
        md_path = out_dir / 'digest.md'
        md_path.write_text(md)
        outputs.append(md_path)

    if 'html' in formats:
        html = HTML_TEMPLATE.render(title=title, items=items, generated_at=generated_at)
        html_path = out_dir / 'digest.html'
        html_path.write_text(html)
        outputs.append(html_path)

    return outputs
