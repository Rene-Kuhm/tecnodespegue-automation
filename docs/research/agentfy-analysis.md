# Agentfy Analysis

**Repo**: https://github.com/Agentfy-io/Agentfy
**Tipo**: Multi-Agent System for Social Media (Python, open source)

## Qué es

Sistema multi-agente con MCP (Model Context Protocol) para automatizar tareas en redes sociales. Usa LLMs para traducir intenciones del usuario en cadenas de tareas.

## Capacidades

| Feature | Descripción |
|---------|-------------|
| Buyer Targeting | Encuentra clientes potenciales en IG/TikTok y les envía DM |
| Cross-Platform Promo | Publica contenido promocional en múltiples redes |
| Content Transformation | Transforma ideas/videos en posts optimizados por plataforma |
| Auto-Messaging | Responde DMs automáticamente en idioma del cliente |
| Creator Discovery | Encuentra influencers para campañas |

## Stack técnico

- Python 3.11+
- OpenAI + Anthropic como LLMs
- TikHub API para datos de TikTok
- Google APIs para YouTube
- Tweepy para X (Twitter)
- FastAPI + Streamlit para interfaz
- Pydantic para configuración

## Agentes disponibles

- Instagram: crawler, analysis, interactive (DMs, posts)
- TikTok: crawler, analysis, interactive (videos, DMs)
- YouTube: crawler, analysis, interactive
- X (Twitter): crawler, analysis, interactive
- Facebook: interactive
- LinkedIn: crawler, analysis
- Discord, Telegram, WhatsApp, Quora, Amazon, Douyin: stubs

## Comparación con nuestro setup actual

| Aspecto | TecnoDespegue actual | Agentfy |
|---------|---------------------|---------|
| Generación de contenido | LLM + FLUX + edge-tts + ffmpeg → video reel | Solo texto/imagen via LLM |
| Publicación | Postiz CLI (schedule) | APIs directas por plataforma |
| Video | Sí (reel 9:16 completo) | No genera video |
| Análisis | No | Sí (crawlers + analysis) |
| DMs automáticos | No | Sí |
| Tendencias | No | Sí (crawlers) |
| Multi-agente | No (script lineal) | Sí (perception→reasoning→action) |

## Qué podemos tomar

1. **Crawler de tendencias**: Adaptar su sistema de análisis de trending topics para alimentar nuestro generador de contenido con temas relevantes
2. **Análisis de engagement**: Sus módulos de analysis podrían medir qué tipo de contenido funciona mejor
3. **DMs automáticos**: Responder mensajes en IG/TikTok automáticamente
4. **Architecture pattern**: Su patrón Perception→Reasoning→Action→Memory es bueno para organizar agentes

## Qué NO nos sirve

- Su publicación es inferior (no genera video, nosotros sí)
- Requiere APIs directas de cada plataforma (OAuth flows complejos vs Postiz que ya los maneja)
- Stack pesado (FastAPI + Streamlit + DB) vs nuestro approach ligero
- Hardcoded credentials en el código (mala práctica)

## Recomendación

**No reemplazar** nuestro pipeline con Agentfy. En cambio:
1. Extraer ideas del módulo de **trending analysis** para mejorar la selección de temas
2. Considerar agregar **DM automation** como feature futura
3. Usar su patrón de **agent registry** si escalamos a más agentes
