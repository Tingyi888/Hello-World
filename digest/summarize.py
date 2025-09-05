from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import os
import math

from tenacity import retry, wait_exponential, stop_after_attempt


@dataclass
class ScoredSummary:
    bullet: str
    relevance: float


def _extractive_summary(text: str, max_sentences: int = 3) -> str:
    # A very small extractive heuristic: pick first N sentences
    import re
    sentences = re.split(r'[\.!?]\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    return ' '.join(sentences[:max_sentences]) if sentences else text[:300]


def summarize_and_score_locally(title: str, abstract: str, keywords: List[str]) -> ScoredSummary:
    title_lower = title.lower()
    abstract_lower = abstract.lower()
    # relevance: keyword hit ratio in title+abstract
    tokens = set(k.strip().lower() for k in keywords if k.strip())
    if not tokens:
        score = 0.5
    else:
        hit = sum(1 for t in tokens if t in title_lower or t in abstract_lower)
        score = min(1.0, 0.3 + 0.7 * (hit / max(1, len(tokens))))
    summary = _extractive_summary(abstract, max_sentences=2)
    bullet = f"- [{title}]: {summary}"
    return ScoredSummary(bullet=bullet, relevance=score)


def _get_openai_client():
    try:
        import openai
    except Exception:
        return None
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    openai.api_key = api_key
    return openai


@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def summarize_and_score_llm(title: str, abstract: str, keywords: List[str], model: str, max_tokens: int, temperature: float) -> ScoredSummary:
    client = _get_openai_client()
    if client is None:
        return summarize_and_score_locally(title, abstract, keywords)
    prompt = (
        "You are a research assistant. Given a paper title and abstract, "
        "write one concise Chinese bullet (<=40 chars) highlighting novelty, and provide a relevance score (0-1) against the given research interests.\n\n"
        f"Interests: {', '.join(keywords)}\n"
        f"Title: {title}\n"
        f"Abstract: {abstract}\n\n"
        "Return JSON: {bullet: string, relevance: number}."
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = resp.choices[0].message.content
        import json
        data = json.loads(content)
        bullet = data.get('bullet') or _extractive_summary(abstract, 2)
        relevance = float(data.get('relevance', 0.6))
        relevance = max(0.0, min(1.0, relevance))
        return ScoredSummary(bullet=f"- [{title}]: {bullet}", relevance=relevance)
    except Exception:
        return summarize_and_score_locally(title, abstract, keywords)
