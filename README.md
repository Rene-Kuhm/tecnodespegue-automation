# TecnoDespegue Automation

Pipeline de automatización de contenido para redes sociales de [TecnoDespegue](https://tecnodespegue.com).

## Qué hace

Genera y publica contenido automático 4 veces al día en **Instagram, Facebook, TikTok y YouTube**:

1. **Texto**: Genera contenido profesional con LLM (OpenRouter)
2. **Narración**: Crea guión de locución en español argentino
3. **Imagen**: Genera imagen 1080x1080 con FLUX.2 Klein
4. **Voz**: Text-to-Speech con edge-tts (voz argentina)
5. **Video**: Reel 9:16 (1080x1920) con Ken Burns + audio narrado
6. **Publicación**: Sube a Postiz → publica en todas las plataformas
7. **Discord**: Notifica en el server de la comunidad
8. **Obsidian**: Guarda registro en vault

## Stack

| Componente | Tecnología |
|-----------|-----------|
| Texto/Narración | OpenRouter (gpt-oss-120b) |
| Imagen | FLUX.2 Klein 4B via OpenRouter |
| Voz | edge-tts (es-AR-TomasNeural) |
| Video | ffmpeg (Ken Burns + blur background) |
| Publicación | Postiz CLI |
| Orquestación | Python + cron |
| Bot Discord | discord.py |

## Scripts

- `scripts/daily-post.py` — Pipeline completo: texto → narración → imagen → voz → video → publicar
- `scripts/postiz-publish.py` — Publicador multi-plataforma con guards de media
- `scripts/postiz-publish.sh` — Versión shell del publicador
- `scripts/tecno-bot.py` — Bot de Discord (bienvenida, auto-rol)

## Cron Schedule (UTC → Argentina)

| UTC | ARG | Tipo |
|-----|-----|------|
| 12:00 | 9:00 AM | Tip técnico |
| 15:00 | 12:00 PM | Caso de uso |
| 22:00 | 7:00 PM | Educativo |
| 00:00 | 9:00 PM | Promoción |

## Setup

1. Copiar `scripts/.env.example` a `.env`
2. Completar las API keys
3. Instalar dependencias: `pip install edge-tts requests`, `apt install ffmpeg`
4. Configurar cron jobs

## Plataformas protegidas

El publicador tiene guards: si no hay media (imagen/video), **NO publica** en Instagram, TikTok ni YouTube (que lo requieren). Solo publica en Facebook (acepta texto solo).

## Roadmap

- [ ] Integrar análisis de tendencias para contenido más relevante
- [ ] A/B testing de formatos de contenido
- [ ] Analytics de engagement por plataforma
- [ ] Multi-agente con CrewAI para estrategia de contenido
- [ ] Respuestas automáticas a DMs/comentarios

## Research

Ver `docs/research/` para análisis de herramientas como Agentfy, CrewAI, n8n.

## Licencia

MIT
