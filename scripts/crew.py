#!/usr/bin/env python3
"""
Multi-agent content pipeline para TecnoDespegue.
3 agentes: Estratega → Redactor → Editor
Sin dependencias extra — usa OpenRouter directamente.
"""
import json
import urllib.request

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"


def _call_llm(api_key, system, user, max_tokens=400):
    data = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        OPENROUTER_URL, data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())
    return result["choices"][0]["message"]["content"].strip()


def agent_strategist(api_key, content_type, trends_ctx="", github_ctx=""):
    """
    ESTRATEGA: Define el angulo, hook y estructura del post.
    Output: brief creativo para el redactor.
    """
    system = (
        "Sos el Director de Estrategia de Contenido de TecnoDespegue, "
        "agencia argentina de software a medida.\n"
        "Tu trabajo: analizar tendencias y contexto para definir el MEJOR angulo "
        "para un post que genere engagement y leads.\n"
        "Publico: duenos de pymes y startups argentinas.\n"
        "Output: un brief creativo de 3-5 lineas con:\n"
        "1. ANGULO: el enfoque especifico (no generico)\n"
        "2. HOOK: la primera frase que atrapa\n"
        "3. TENSION: que dolor o deseo toca\n"
        "4. CTA: que accion queremos del lector\n"
        "Responde SOLO con el brief, sin explicaciones."
    )
    
    user_parts = [f"Tipo de contenido: {content_type}"]
    if trends_ctx:
        user_parts.append(f"TENDENCIAS DE HOY:\n{trends_ctx}")
    if github_ctx:
        user_parts.append(f"TRABAJO REAL RECIENTE:\n{github_ctx}")
    user_parts.append(
        "Crea un brief creativo que NO suene generico. "
        "Debe estar anclado en algo real, actual, especifico."
    )
    
    brief = _call_llm(api_key, system, "\n\n".join(user_parts), max_tokens=250)
    return brief


def agent_writer(api_key, brief, style_prompt, agency_context):
    """
    REDACTOR: Escribe el post siguiendo el brief del estratega.
    Output: texto del post (120-180 palabras).
    """
    system = (
        "Sos el Redactor Senior de TecnoDespegue. "
        "Escribis posts que generan leads reales.\n"
        + agency_context + "\n\n"
        "REGLA CRITICA: segui el brief del estratega al pie de la letra. "
        "El hook que te da ES el hook que usas. No lo cambies."
    )
    
    user = (
        f"BRIEF DEL ESTRATEGA:\n{brief}\n\n"
        f"ESTILO REQUERIDO:\n{style_prompt}\n\n"
        "Escribi el post. SOLO texto, sin markdown, sin asteriscos, sin titulos. "
        "120-180 palabras. Cada palabra cuenta."
    )
    
    post = _call_llm(api_key, system, user, max_tokens=500)
    return post


def agent_editor(api_key, post_text, content_type):
    """
    EDITOR: Revisa y pule el post. Verifica reglas, mejora copy.
    Output: post final corregido.
    """
    system = (
        "Sos el Editor Jefe de TecnoDespegue. Tu trabajo es PULIR posts.\n"
        "CHECKLIST (verificar TODO):\n"
        "- Primera linea es un HOOK fuerte (sin saludo, sin 'en el mundo actual')\n"
        "- Sin markdown, sin asteriscos, sin guiones de lista\n"
        "- Sin frases prohibidas: 'en el mundo actual', 'la tecnologia avanza', "
        "'el futuro digital', 'hoy en dia', 'en la era de'\n"
        "- Tiene CTA concreto al final (tecnodespegue.com o WhatsApp 2334409838)\n"
        "- 3-4 hashtags al final, siempre incluye #tecnodespegue\n"
        "- Maximo 180 palabras\n"
        "- Tono argentino natural, no robotico\n"
        "- Sin emojis excesivos (maximo 2-3)\n"
        "- Sin numeros de telefono en el cuerpo (solo en CTA final)\n\n"
        "Si el post cumple todo, devolvelo tal cual con mejoras minimas de copy. "
        "Si tiene errores, corregilo. "
        "Responde SOLO con el post final, nada mas."
    )
    
    user = (
        f"TIPO: {content_type}\n\n"
        f"POST A REVISAR:\n{post_text}"
    )
    
    final = _call_llm(api_key, system, user, max_tokens=500)
    return final


def generate_post_multiagent(api_key, content_type, style_prompt, agency_context,
                              trends_ctx="", github_ctx=""):
    """
    Pipeline completo: Estratega → Redactor → Editor.
    Retorna el post final pulido.
    """
    print("  [Estratega] Definiendo angulo...")
    brief = agent_strategist(api_key, content_type, trends_ctx, github_ctx)
    print(f"  Brief: {brief[:80]}...")
    
    print("  [Redactor] Escribiendo post...")
    draft = agent_writer(api_key, brief, style_prompt, agency_context)
    print(f"  Borrador: {len(draft.split())} palabras")
    
    print("  [Editor] Revisando y puliendo...")
    final = agent_editor(api_key, draft, content_type)
    print(f"  Final: {len(final.split())} palabras")
    
    return final


if __name__ == "__main__":
    import os
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        print("Set OPENROUTER_API_KEY")
    else:
        result = generate_post_multiagent(
            key, "tip_tecnico",
            "Post de autoridad posicionando a TecnoDespegue como expertos.",
            "Sos TecnoDespegue, agencia argentina de software.",
        )
        print("\n" + result)
