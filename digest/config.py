from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml


@dataclass
class ArxivConfig:
    enable: bool = True
    keywords: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=lambda: ['cs.CL', 'cs.LG', 'cs.AI'])
    max_results: int = 100
    window_days: int = 7
    include_regex: List[str] = field(default_factory=list)
    exclude_regex: List[str] = field(default_factory=list)


@dataclass
class ScoringConfig:
    use_llm: bool = False
    llm_model: str = 'gpt-4o-mini'
    max_tokens: int = 512
    temperature: float = 0.2
    top_k: int = 15
    min_relevance: float = 0.55


@dataclass
class RenderConfig:
    max_per_section: int = 20
    output_dir: str = 'out'
    formats: List[str] = field(default_factory=lambda: ['md', 'html'])


@dataclass
class TelegramConfig:
    enable: bool = False
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None


@dataclass
class EmailConfig:
    enable: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    mail_to: Optional[str] = None


@dataclass
class DeliverConfig:
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    email: EmailConfig = field(default_factory=EmailConfig)


@dataclass
class AppConfig:
    title: str = '每周科研周报'
    timezone: str = 'UTC'
    sources: Dict[str, Any] = field(default_factory=dict)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    render: RenderConfig = field(default_factory=RenderConfig)
    deliver: DeliverConfig = field(default_factory=DeliverConfig)

    @staticmethod
    def from_yaml(path: str | Path) -> 'AppConfig':
        data = yaml.safe_load(Path(path).read_text())
        arxiv_dict = data.get('sources', {}).get('arxiv', {})
        sources = {
            'arxiv': ArxivConfig(**arxiv_dict),
        }
        scoring = ScoringConfig(**data.get('scoring', {}))
        render = RenderConfig(**data.get('render', {}))
        deliver = DeliverConfig(
            telegram=TelegramConfig(**data.get('deliver', {}).get('telegram', {})),
            email=EmailConfig(**data.get('deliver', {}).get('email', {})),
        )
        return AppConfig(
            title=data.get('title', '每周科研周报'),
            timezone=data.get('timezone', 'UTC'),
            sources=sources,
            scoring=scoring,
            render=render,
            deliver=deliver,
        )

