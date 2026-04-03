#!/usr/bin/env python3
"""
Crawler de tendencias para alimentar el pipeline de contenido.
Busca trending topics en tech/negocios desde fuentes gratuitas.
"""
import urllib.request
import json
import re
import random
from datetime import datetime, timezone, timedelta

OPENROUTER_KEY = None  # Set by caller
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def fetch_hackernews_trends(limit=10):
    """Top stories de Hacker News — tech trends reales."""
    try:
        req = urllib.request.Request(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers={"User-Agent": "TecnoDespegue-Bot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            ids = json.loads(r.read())[:limit]
        
        stories = []
        for sid in ids:
            req2 = urllib.request.Request(
                f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                headers={"User-Agent": "TecnoDespegue-Bot/1.0"}
            )
            with urllib.request.urlopen(req2, timeout=5) as r:
                item = json.loads(r.read())
                if item and item.get("title"):
                    stories.append({
                        "title": item["title"],
                        "score": item.get("score", 0),
                        "url": item.get("url", ""),
                    })
        return stories
    except Exception as e:
        print(f"  HN error: {e}")
        return []


def fetch_devto_trends(limit=8):
    """Artículos trending de dev.to — tendencias dev."""
    try:
        req = urllib.request.Request(
            f"https://dev.to/api/articles?top=1&per_page={limit}",
            headers={"User-Agent": "TecnoDespegue-Bot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            articles = json.loads(r.read())
        return [{
            "title": a["title"],
            "tags": a.get("tag_list", []),
            "reactions": a.get("positive_reactions_count", 0),
        } for a in articles]
    except Exception as e:
        print(f"  dev.to error: {e}")
        return []


def fetch_github_trending():
    """Repos trending de GitHub via search API."""
    try:
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
        req = urllib.request.Request(
            f"https://api.github.com/search/repositories?q=created:>{week_ago}&sort=stars&order=desc&per_page=8",
            headers={"User-Agent": "TecnoDespegue-Bot/1.0", "Accept": "application/vnd.github.v3+json"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return [{
            "name": r["full_name"],
            "description": r.get("description", "")[:100],
            "stars": r["stargazers_count"],
            "language": r.get("language", "N/A"),
        } for r in data.get("items", [])[:8]]
    except Exception as e:
        print(f"  GitHub trending error: {e}")
        return []


def get_trending_context():
    """Combina todas las fuentes en un contexto de tendencias."""
    print("  Buscando tendencias...")
    hn = fetch_hackernews_trends(8)
    devto = fetch_devto_trends(6)
    gh = fetch_github_trending()
    
    parts = []
    if hn:
        hn_lines = [f"  - {s['title']} (score: {s['score']})" for s in hn[:6]]
        parts.append("TRENDING EN HACKER NEWS:\n" + "\n".join(hn_lines))
    if devto:
        dt_lines = [f"  - {a['title']} (tags: {', '.join(a['tags'][:3])})" for a in devto[:5]]
        parts.append("TRENDING EN DEV.TO:\n" + "\n".join(dt_lines))
    if gh:
        gh_lines = [f"  - {r['name']} ({r['language']}, {r['stars']}★): {r['description']}" for r in gh[:5]]
        parts.append("REPOS TRENDING EN GITHUB:\n" + "\n".join(gh_lines))
    
    ctx = "\n\n".join(parts) if parts else ""
    if ctx:
        print(f"  Tendencias encontradas: {len(hn)} HN, {len(devto)} dev.to, {len(gh)} GitHub")
    else:
        print("  No se encontraron tendencias")
    return ctx


def select_trending_topic(trends_ctx, content_type, api_key):
    """Usa LLM para seleccionar el trending topic más relevante para el tipo de contenido."""
    if not trends_ctx or not api_key:
        return None
    
    prompt = (
        f"Analiza estas tendencias tecnologicas de hoy:\n\n{trends_ctx}\n\n"
        f"Tipo de contenido a crear: {content_type}\n"
        f"Audiencia: duenos de pymes y startups argentinas\n\n"
        "Selecciona LA tendencia mas relevante para este publico y tipo de contenido. "
        "Responde con UNA SOLA LINEA: el tema adaptado al lenguaje de negocios argentino. "
        "No expliques, no enumeres, solo el tema en una linea."
    )
    
    try:
        data = json.dumps({
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
        }).encode()
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
        topic = result["choices"][0]["message"]["content"].strip()
        topic = re.sub(r'["*#]', '', topic).strip()
        if len(topic) > 10:
            print(f"  Trending topic seleccionado: {topic[:80]}")
            return topic
    except Exception as e:
        print(f"  Error seleccionando trending: {e}")
    return None


if __name__ == "__main__":
    ctx = get_trending_context()
    print("\n" + ctx)
