from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from typing import List, Optional, Iterable

import arxiv
from dateutil import tz


@dataclass
class Paper:
    id: str
    title: str
    summary: str
    authors: List[str]
    published: datetime
    updated: datetime
    primary_category: Optional[str]
    link_pdf: Optional[str]
    link_abs: Optional[str]


def _build_query(keywords: List[str], categories: List[str]) -> str:
    # Keywords: OR within an item, AND across tokens
    keyword_clauses: List[str] = []
    for kw in keywords:
        kw = kw.strip()
        if not kw:
            continue
        if ',' in kw:
            ors = ' OR '.join([f'all:"{o.strip()}"' for o in kw.split(',') if o.strip()])
            keyword_clauses.append(f'({ors})')
        else:
            keyword_clauses.append(f'all:"{kw}"')
    cat_clause = ' OR '.join([f'cat:{c}' for c in categories]) if categories else ''
    parts = [p for p in [' AND '.join(keyword_clauses), f'({cat_clause})' if cat_clause else ''] if p]
    return ' AND '.join(parts) if parts else 'all:*'


def fetch_arxiv_recent(keywords: List[str], categories: List[str], window_days: int, max_results: int) -> List[Paper]:
    query = _build_query(keywords, categories)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    client = arxiv.Client()
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=window_days)
    papers: List[Paper] = []
    for result in client.results(search):
        if result.published and result.published.replace(tzinfo=timezone.utc) < window_start:
            # results are sorted desc; we can early break when older than window
            break
        papers.append(Paper(
            id=result.get_short_id(),
            title=result.title.strip(),
            summary=result.summary.strip(),
            authors=[a.name for a in result.authors],
            published=result.published.replace(tzinfo=timezone.utc) if result.published else now,
            updated=result.updated.replace(tzinfo=timezone.utc) if result.updated else now,
            primary_category=(result.primary_category or {}).get('term') if isinstance(result.primary_category, dict) else getattr(result, 'primary_category', None),
            link_pdf=getattr(result, 'pdf_url', None),
            link_abs=getattr(result, 'entry_id', None),
        ))
    return papers


def filter_papers(papers: List[Paper], include_regex: List[str] | None, exclude_regex: List[str] | None) -> List[Paper]:
    def matches_any(patterns: Iterable[str], text: str) -> bool:
        for p in patterns:
            if re.search(p, text, flags=re.IGNORECASE):
                return True
        return False

    included = papers
    if include_regex:
        included = [p for p in included if matches_any(include_regex, p.title + '\n' + p.summary)]
    if exclude_regex:
        included = [p for p in included if not matches_any(exclude_regex, p.title + '\n' + p.summary)]
    return included
