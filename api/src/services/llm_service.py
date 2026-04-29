"""
Service LLM — Extraction profil CV + re-ranking via Gemini
Fournit deux fonctions :
  - extract_cv_profile : analyse structurée du CV (titre, compétences, localisation…)
  - rerank_jobs        : classement final des offres DB + live avec explication courte
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Singleton client
_gemini_model = None


def _get_gemini():
    global _gemini_model
    if not GEMINI_API_KEY:
        return None
    if _gemini_model is None:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            _gemini_model = genai.GenerativeModel(GEMINI_MODEL)
            logger.info(f"Gemini model loaded: {GEMINI_MODEL}")
        except Exception as e:
            logger.warning(f"Gemini unavailable: {e}")
            return None
    return _gemini_model


def _strip_markdown(raw: str) -> str:
    """Remove ```json ... ``` wrapping if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove first and last fence lines
        lines = [l for l in lines if not l.startswith("```")]
        raw = "\n".join(lines).strip()
    return raw


def extract_cv_profile(cv_text: str) -> dict:
    """
    Parse le texte du CV via Gemini et retourne un profil structuré.
    Retourne {} si Gemini n'est pas configuré ou en cas d'erreur.
    """
    model = _get_gemini()
    if not model:
        return {}

    prompt = f"""Analyse ce CV et extrais les informations suivantes sous forme JSON strict (pas de markdown, uniquement le JSON) :
{{
  "job_title": "Intitulé du poste principal ou rôle recherché",
  "skills": ["compétence1", "compétence2"],
  "years_experience": 0,
  "location": "Ville ou pays mentionné",
  "languages": ["langue1", "langue2"]
}}

CV (3000 premiers caractères) :
{cv_text[:3000]}

Retourne UNIQUEMENT l'objet JSON, sans explication."""

    try:
        response = model.generate_content(prompt)
        raw = _strip_markdown(response.text)
        profile = json.loads(raw)
        logger.info(f"CV profile extracted: job_title={profile.get('job_title')}")
        return profile
    except Exception as e:
        logger.warning(f"CV profile extraction failed: {e}")
        return {}


def rerank_jobs(cv_text: str, profile: dict, jobs: list, top_k: int) -> list:
    """
    Re-classe les offres (DB + live) via Gemini et ajoute une explication courte.
    Si Gemini n'est pas disponible ou échoue, retourne les jobs triés par score cosine.
    """
    model = _get_gemini()
    if not model or not jobs:
        return jobs[:top_k]

    # Résumé du profil candidat
    profile_summary = (
        f"Poste recherché : {profile.get('job_title', 'Non spécifié')}\n"
        f"Compétences : {', '.join(profile.get('skills', [])[:8])}\n"
        f"Expérience : {profile.get('years_experience', '?')} an(s)\n"
        f"Localisation : {profile.get('location', 'Non spécifié')}"
    )

    # Préparer la liste des offres à classer (sans colonnes inutiles)
    jobs_for_ranking = [
        {
            "id": j.get("id"),
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "location": j.get("location", ""),
            "description": (j.get("description") or "")[:400],
            "source_type": j.get("source_type", "database"),
        }
        for j in jobs
    ]

    prompt = f"""Tu es un expert en recrutement. Classe ces offres d'emploi par pertinence pour ce candidat.

PROFIL CANDIDAT :
{profile_summary}

EXTRAIT DU CV :
{cv_text[:1500]}

OFFRES À CLASSER :
{json.dumps(jobs_for_ranking, ensure_ascii=False)}

Retourne un tableau JSON des {top_k} offres les plus pertinentes, du plus au moins pertinent.
Chaque élément doit contenir :
- "id" : l'id de l'offre (exactement comme dans la liste)
- "ai_score" : score de pertinence de 0.0 à 1.0
- "ai_match_reason" : une phrase courte en français expliquant la correspondance

Retourne UNIQUEMENT le tableau JSON, sans markdown ni explication."""

    try:
        response = model.generate_content(prompt)
        raw = _strip_markdown(response.text)
        logger.info(f"Gemini raw response (first 300 chars): {raw[:300]}")
        ranking = json.loads(raw)

        # Index par id normalisé en int pour absorber les "42", 42.0, 42 de Gemini
        def _norm_id(v):
            try:
                return int(float(v))
            except (TypeError, ValueError):
                return v

        jobs_by_id = {_norm_id(j.get("id")): j for j in jobs}
        logger.info(f"Reranking: {len(jobs)} jobs in pool, Gemini returned {len(ranking)} items")

        result = []
        for item in ranking[:top_k]:
            job_id = _norm_id(item.get("id"))
            if job_id in jobs_by_id:
                job = dict(jobs_by_id[job_id])
                job["ai_match_reason"] = item.get("ai_match_reason")
                job["score"] = round(float(item.get("ai_score", job.get("score", 0.0))), 4)
                result.append(job)
            else:
                logger.warning(f"Gemini returned unknown id={job_id!r}, skipping")

        logger.info(f"Gemini reranking: {len(result)} jobs matched and returned")
        return result

    except Exception as e:
        logger.warning(f"Gemini reranking failed: {e}")
        # Graceful fallback : tri cosine original
        return sorted(jobs, key=lambda x: x.get("score", 0), reverse=True)[:top_k]
