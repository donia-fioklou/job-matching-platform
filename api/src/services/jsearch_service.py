"""
Service JSearch — Recherche d'offres fraîches via RapidAPI JSearch
Utilisé en complément de la recherche vectorielle DB quand Gemini est activé.
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY")
JSEARCH_HOST = "jsearch.p.rapidapi.com"
JSEARCH_TIMEOUT = 8.0  # secondes


async def search_fresh_jobs(job_title: str, location: str = "", top_k: int = 10) -> list:
    """
    Recherche des offres fraîches via JSearch (RapidAPI).
    Retourne [] si la clé API n'est pas configurée ou en cas d'erreur.
    """
    if not JSEARCH_API_KEY or not job_title:
        return []

    query = f"{job_title} in {location}" if location else job_title

    try:
        async with httpx.AsyncClient(timeout=JSEARCH_TIMEOUT) as client:
            resp = await client.get(
                f"https://{JSEARCH_HOST}/search",
                params={
                    "query": query,
                    "page": "1",
                    "num_pages": "1",
                    "date_posted": "month",
                },
                headers={
                    "x-rapidapi-key": JSEARCH_API_KEY,
                    "x-rapidapi-host": JSEARCH_HOST,
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        logger.warning("JSearch API timeout")
        return []
    except Exception as e:
        logger.warning(f"JSearch API error: {e}")
        return []

    results = []
    for i, item in enumerate(data.get("data", [])[:top_k]):
        results.append({
            "id": -(i + 1),  # IDs négatifs pour distinguer les offres live des offres DB
            "title": item.get("job_title", ""),
            "company": item.get("employer_name", ""),
            "location": _format_location(item),
            "source": "JSearch (live)",
            "job_url": item.get("job_apply_link") or item.get("job_google_link", ""),
            "scraped_at": None,
            "has_full_description": bool(item.get("job_description")),
            "contract_type": item.get("job_employment_type"),
            "experience_level": None,
            "salary_range": _format_salary(item),
            "description": (item.get("job_description") or "")[:500],
            "score": 0.0,  # Sera remplacé par Gemini
            "ai_match_reason": None,
            "source_type": "live_search",
        })

    logger.info(f"JSearch returned {len(results)} live jobs for query: {query!r}")
    return results


def _format_location(item: dict) -> str:
    parts = [item.get("job_city"), item.get("job_state"), item.get("job_country")]
    return ", ".join(p for p in parts if p)


def _format_salary(item: dict) -> Optional[str]:
    min_s = item.get("job_min_salary")
    max_s = item.get("job_max_salary")
    currency = item.get("job_salary_currency", "")
    period = item.get("job_salary_period", "")
    if min_s and max_s:
        return f"{min_s}–{max_s} {currency} / {period}".strip(" /")
    return None
