import json
#!/usr/bin/env python3
import subprocess, sys, json, urllib.request, urllib.error, os, base64, re, random
from datetime import datetime, timezone, timedelta

# Multi-agent & trending modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from trending import get_trending_context, select_trending_topic
    from crew import generate_post_multiagent
    MULTIAGENT_AVAILABLE = True
    print("[modules] trending + crew loaded")
except ImportError as e:
    MULTIAGENT_AVAILABLE = False
    print(f"[modules] fallback mode: {e}")

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_KEY:
    print("[ERROR] OPENROUTER_API_KEY no configurada. Abortando.")
    import sys; sys.exit(1)
POSTIZ_KEY     = os.environ.get("POSTIZ_API_KEY", "")
DISCORD_TOKEN  = os.environ.get("DISCORD_TOKEN", "")
OBSIDIAN_VAULT = "/home/node/clawd/brain"
DISCORD_CHANNELS = {
    "tip_tecnico": "1489368561960091699",
    "caso_uso":    "1489368562974986354",
    "educativo":   "1489368563805454487",
    "promocion":   "1489368564711428156",
}
PUBLISH_SCRIPT = "/home/node/clawd/scripts/postiz-publish.py"
TEXT_MODEL     = "openai/gpt-4o-mini"
COPY_MODEL     = "openai/gpt-4o-mini"
IMAGE_MODEL    = "black-forest-labs/flux.2-klein-4b"
TTS_VOICE      = "es-AR-TomasNeural"
NPM_BIN        = "/home/node/.npm-global/bin"
POSTIZ_BIN     = f"{NPM_BIN}/postiz"
ENV            = {
    **os.environ,
    "POSTIZ_API_KEY": POSTIZ_KEY,
    "PATH": f"{NPM_BIN}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
}

GITHUB_USER = "Rene-Kuhm"

def fetch_github_context():
    """Fetch real recent activity from GitHub to ground posts in actual work."""
    try:
        import urllib.request as _ur, json as _json
        headers = {"User-Agent": "TecnoDespegue-Bot/1.0"}
        req = _ur.Request(
            f"https://api.github.com/users/{GITHUB_USER}/events?per_page=30",
            headers=headers
        )
        with _ur.urlopen(req, timeout=8) as r:
            events = _json.loads(r.read())
        recent_work = []
        repos_seen = set()
        for e in events:
            repo = e["repo"]["name"].split("/")[-1]
            if repo in repos_seen:
                continue
            if e["type"] == "PushEvent":
                commits = e["payload"].get("commits", [])
                msgs = [c["message"].split("\n")[0][:70] for c in commits[:2]]
                if msgs:
                    recent_work.append(f"- Trabajando en {repo!r}: {'; '.join(msgs)}")
                    repos_seen.add(repo)
            elif e["type"] == "CreateEvent" and e["payload"].get("ref_type") == "repository":
                recent_work.append(f"- Nuevo proyecto creado: {repo!r}")
                repos_seen.add(repo)
            if len(recent_work) >= 5:
                break
        req2 = _ur.Request(
            f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=6&sort=updated",
            headers=headers
        )
        with _ur.urlopen(req2, timeout=8) as r:
            repos = _json.loads(r.read())
        repo_lines = []
        for rp in repos[:5]:
            lang = rp.get("language") or "varios"
            desc = rp.get("description") or ""
            repo_lines.append(f"  - {rp['name']} ({lang}){': ' + desc[:55] if desc else ''}")
        ctx_parts = []
        if recent_work:
            ctx_parts.append("ACTIVIDAD RECIENTE EN GITHUB:\n" + "\n".join(recent_work))
        if repo_lines:
            ctx_parts.append("PROYECTOS ACTIVOS:\n" + "\n".join(repo_lines))
        return "\n\n".join(ctx_parts)
    except Exception:
        return ""

ARG_HOUR = (datetime.now(timezone.utc) - timedelta(hours=3)).hour
ARG_NOW  = datetime.now(timezone.utc) - timedelta(hours=3)
TS       = datetime.now().strftime("%Y%m%d_%H%M%S")

AGENCY_CONTEXT = (
    "Sos la voz de TecnoDespegue (tecnodespegue.com), "
    "agencia argentina de desarrollo de software a medida y automatizacion con IA.\\n\\n"
    "MISION DE CADA POST: que un dueno de empresa piense 'este problema lo tengo yo, "
    "y TecnoDespegue puede resolverlo'. Nada mas. Nada menos.\\n\\n"
    "IDENTIDAD:\\n"
    "- Expertos reales. No vendemos humo. Entregamos software que funciona y dura.\\n"
    "- Tono: directo, sin tecnicismos vacios, como un asesor de confianza.\\n"
    "- Hablamos con el dueno de empresa, el director, el fundador. No con developers.\\n"
    "- NUNCA sonamos como un blog de programacion. Sonamos como una agencia que genera resultados.\\n\\n"
    "PUBLICO OBJETIVO: duenos de pymes, fundadores de startups, directores comerciales "
    "que necesitan tecnologia que realmente funcione para su negocio.\\n\\n"
    "SERVICIOS: software a medida (frontend/backend), apps para empresas y startups, "
    "automatizaciones con IA, integracion de sistemas, consultoria tecnica.\\n\\n"
    "DIFERENCIADOR: arquitecturas correctas desde el dia uno. "
    "Software que no se rompe en 6 meses. El mismo nivel que las grandes empresas, "
    "disponible para pymes y startups.\\n\\n"
    "CONTACTO: tecnodespegue.com | contacto@tecnodespegue.com | WhatsApp: 2334409838\\n\\n"
    "REGLAS OBLIGATORIAS:\\n"
    "- HOOK en la primera linea: sin saludos, sin 'hola', sin 'en el mundo actual'.\\n"
    "- Primera frase es lo mas importante. Genera tension, urgencia o curiosidad real.\\n"
    "- PROHIBIDO: 'en el mundo actual', 'la tecnologia avanza', 'el futuro digital', 'hoy en dia'.\\n"
    "- Sin markdown: texto corrido, sin asteriscos, sin guiones de lista.\\n"
    "- Maximo 180 palabras. Cada una cuenta.\\n"
    "- CTA especifico en la ultima linea: tecnodespegue.com o WhatsApp 2334409838.\\n"
    "- 3-4 hashtags al final: siempre #tecnodespegue + relacionados al tema del post.\\n"
    "- Termina con accion concreta: 'Escribinos', 'Visitanos', 'Agendemos una llamada'."
)

# Determinar tipo de contenido
current_weekday = ARG_NOW.weekday()  # 0=lunes, 1=martes, ..., 6=domingo
topic = None
if current_weekday == 1 or current_weekday == 3:  # Martes o jueves
    content_type   = "tutorial_programacion"
elif current_weekday == 5:  # Sabado
    content_type   = "tech_news_2026"
elif 7 <= ARG_HOUR < 11:
    content_type   = "tip_tecnico"
    style          = (
        "Escribi un post de AUTORIDAD que posicione a TecnoDespegue como expertos.\\n"
        "Formula OBLIGATORIA (cada paso debe estar):\\n"
        "1. HOOK VIRAL (primera linea): pregunta o afirmacion que GENERE CURIOSIDAD o INQUIETUD. "
        "Tipo: 'Nadie te dice esto sobre...', '3 senales de que tu empresa necesita esto', "
        "'Si tenes un negocio y no haces esto, estas perdiendo plata'.\\n"
        "2. PROBLEMA ESPECIFICO: nombra el dolor real de empresas (no generico).\\n"
        "3. POR QUE PASA: causa raiz en terminos de negocio (no tecnicos).\\n"
        "4. COMO LO RESOLVEMOS: solucion concreta de TecnoDespegue.\\n"
        "5. CTA: 'Escribinos sin compromiso: tecnodespegue.com'\\n"
        "Tono: experto argentino, directo, sin relleno."
    )
    image_style    = (
        "split composition: left side shows a frustrated business owner at laptop with red error screens, "
        "right side shows confident developer team celebrating a solved problem, "
        "dark background, electric blue and green accent lighting, "
        "cinematic contrast, premium corporate photography, 8K"
    )
    narration_tone = "consultor experto hablando directo al dueno de una empresa, seguro y claro"

elif 11 <= ARG_HOUR < 15:
    content_type   = "caso_uso"
    style          = (
        "Escribi un caso de exito de TecnoDespegue en formato storytelling.\\n"
        "El lector debe pensar: 'tengo ese problema, necesito llamarlos'.\\n"
        "Formula OBLIGATORIA:\\n"
        "1. HOOK: 'Esta empresa perdia $X al mes hasta que...', 'Como pasamos de [A] a [B]'.\\n"
        "2. INDUSTRIA Y DOLOR: sector especifico + problema real.\\n"
        "3. LO QUE ENCONTRAMOS: la causa raiz (en terminos de negocio).\\n"
        "4. SOLUCION: que construimos (app, automatizacion, integracion).\\n"
        "5. RESULTADO: numero concreto (ahorro, tiempo, % de mejora).\\n"
        "6. CTA: 'Tu empresa puede ser la proxima. Escribinos: tecnodespegue.com'\\n"
        "Sectores: retail, logistica, salud, servicios, e-commerce, construccion."
    )
    image_style    = (
        "before and after business transformation: left panel dark chaos with paper processes, "
        "right panel bright modern dashboard with green metrics going up, "
        "Latin American business context, deep blue and electric green palette, "
        "data visualization overlays, premium corporate photography, 8K"
    )
    narration_tone = "como el CEO de TecnoDespegue presentando un caso de exito a inversores, orgulloso y preciso"

elif 15 <= ARG_HOUR < 21:
    content_type   = "educativo"
    style          = (
        "Escribi un post que haga pensar: 'no sabia esto, mi negocio no escala por esto'.\\n"
        "NO es para devs. Es para decision makers.\\n"
        "Formula OBLIGATORIA:\\n"
        "1. HOOK: 'La razon por la que tu negocio no crece no es... sino esto otro'.\\n"
        "2. VERDAD INCOMODA: algo que la mayoria hace mal.\\n"
        "3. EL COSTO: tiempo/dinero/oportunidades perdidas por hacerlo mal.\\n"
        "4. COMO SE HACE BIEN: lo que hacemos en TecnoDespegue.\\n"
        "5. SENAL DE ALERTA: como saber si tenes este problema.\\n"
        "6. CTA: 'Diagnostico gratuito: tecnodespegue.com'\\n"
        "Temas: software que no escala, procesos manuales, cuando conviene software a medida, IA para reducir costos."
    )
    image_style    = (
        "executive looking at growth chart that suddenly plateaus, dark moody office environment, "
        "overlay of digital infrastructure breaking under pressure, "
        "electric blue warning lights, cinematic composition, "
        "premium business photography with tech elements, 8K"
    )
    narration_tone = "como un asesor de negocios tech que acaba de identificar el problema de una empresa"

else:
    content_type   = "promocion"
    style          = (
        "Escribi un post de ACCION - no inspiracion, ACCION.\\n"
        "El lector tiene que actuar DESPUES de leer.\\n"
        "Formula OBLIGATORIA:\\n"
        "1. HOOK: 'Duplicamos [resultado] en [tiempo] para [tipo de empresa]'.\\n"
        "2. RESULTADO: numero concreto y verificable.\\n"
        "3. PROCESO: que incluye trabajar con nosotros (claro, sin sorpresas).\\n"
        "4. URGENCIA: por que NO actuar cuesta plata.\\n"
        "5. DIFERENCIADOR: que nos hace distintos.\\n"
        "6. CTA: 'Primera llamada sin cargo. Visitanos: tecnodespegue.com'\\n"
        "Tono: directo, sin relleno, propuesta comercial de alto nivel."
    )
    image_style    = (
        "premium dark brand visual: confident tech team in modern office, "
        "screens showing successful deployed applications, "
        "client testimonial overlay in elegant typography, "
        "electric blue and gold color scheme, "
        "ultra premium agency aesthetic, cinematic lighting, 8K"
    )
    narration_tone = "pitch directo de un founder seguro de lo que vende, sin dudar ni decorate"

#Tutoriales de programacion (martes y jueves)
if content_type == "tutorial_programacion":
    tutorial_topics = [
        "Por que el software de tu empresa se rompe a los 6 meses: la causa real",
        "Como una pyme ahorró 20 horas semanales automatizando un proceso manual",
        "Señales de que tu sistema actual ya no puede crecer con tu empresa",
        "Que pasa cuando contratas a la agencia mas barata: lo que no te cuentan",
        "De planilla de Excel a sistema propio: como lo hacemos en TecnoDespegue",
        "Por que tu app tarda en cargar y como eso te esta costando clientes",
        "Integracion de IA en tu negocio: casos reales que generan ROI",
        "El momento exacto en que una pyme necesita software a medida",
        "Por que los sistemas hechos a las apuradas siempre salen el doble de caros",
        "Como medimos el exito de un proyecto: lo que el cliente no ve pero importa",
        "Automatizacion vs contratacion: cuando la tecnologia sale mas barata que una persona",
        "El error que cometen el 90% de las empresas al digitalizar sus procesos",
        "Como construimos un sistema de gestion en tiempo real para una empresa de servicios",
        "Por que no existe el software barato y bueno: la matematica detras de la calidad",
        "Lo que diferencia a una agencia de software real de una fabrica de codigo"
    ]
    topic = random.choice(tutorial_topics)
    
    style = (
        "Escribi un post que posicione a TecnoDespegue como expertos que solucionan "
        "problemas reales de empresas.\\n"
        "El lector debe pensar: 'esto me pasa a mi, tengo que llamarlos'.\\n"
        "Formula OBLIGATORIA:\\n"
        "1. HOOK DIRECTO: nombra el problema especifico sin rodeos. "
        "Tipo: 'Tu empresa pierde plata por esto y probablemente no lo sabes'.\\n"
        "2. POR QUE PASA: causa raiz en lenguaje de negocio, sin jerga tecnica.\\n"
        "3. EL COSTO REAL: cuanto le sale ignorarlo (tiempo, dinero, oportunidades).\\n"
        "4. COMO LO RESOLVEMOS: que hace TecnoDespegue exactamente.\\n"
        "5. RESULTADO CONCRETO: numero o cambio especifico logrado.\\n"
        "6. CTA: 'Diagnostico sin cargo: tecnodespegue.com'\\n"
        "Tono: asesor de negocios argentino, directo, sin humo. No suenas a dev blog."
    )
    image_style = (
        "Argentine business owner at modern desk looking at growing metrics on screen, "
        "confident expression, modern office environment, "
        "deep blue and electric green color palette, "
        "cinematic business photography, success and growth visual, 8K"
    )
    narration_tone = "asesor de negocios argentino que acaba de identificar el problema de una empresa"

# Noticias tech 2026 (sabado)
elif content_type == "tech_news_2026":
    news_topics = [
        "IA para empresas: lo que realmente funciona en 2026 y lo que es marketing",
        "Por que las pymes argentinas que digitalizaron sus procesos crecieron un 40% mas",
        "El software a medida vs los SaaS: cuando conviene cada uno para tu negocio",
        "Automatizacion inteligente: casos reales de empresas que redujeron costos operativos",
        "Por que el 70% de los proyectos de software fallan y como evitarlo",
        "Lo que las empresas mas exitosas de Argentina tienen en comun: sistemas propios",
        "IA en atencion al cliente: cuanto ahorra realmente una empresa madura",
        "Por que el e-commerce que no invierte en tecnologia pierde contra el que si lo hace",
        "Integraciones de sistemas: como las empresas eliminan el trabajo manual en 2026",
        "El costo oculto de los sistemas legacy en empresas argentinas",
        "Por que contratar una agencia de software en lugar de un freelancer",
        "Como las startups que escalan usan la tecnologia para crecer sin contratar mas gente"
    ]
    topic = random.choice(news_topics)
    
    style = (
        "Escribi un post que muestre como las tendencias tecnologicas "
        "impactan directamente en los negocios de hoy.\\n"
        "El lector tiene que pensar: 'si no me muevo ahora, me quedo atras'.\\n"
        "Formula OBLIGATORIA:\\n"
        "1. HOOK: una estadistica real o un hecho que genere urgencia. Sin saludos.\\n"
        "2. QUE ESTA PASANDO: el cambio o tendencia, explicado en lenguaje de negocio.\\n"
        "3. QUIEN YA LO USA: ejemplo de empresa o sector que ya lo implemento.\\n"
        "4. QUE LE PASA AL QUE NO SE ADAPTA: consecuencia real y especifica.\\n"
        "5. COMO AYUDA TECNODESPEGUE: posicion de la agencia frente a esta tendencia.\\n"
        "6. CTA: 'Hablemos de como implementarlo en tu empresa: tecnodespegue.com'\\n"
        "Tono: experto en negocios tech argentino, no periodista de tecnologia."
    )
    image_style = (
        "Argentine business leader looking at future cityscape with digital overlays, "
        "growth charts and automation visualizations floating in air, "
        "confident forward-looking composition, "
        "deep blue and electric green accent lighting, "
        "premium corporate futurism photography, 8K"
    )
    narration_tone = "director de estrategia de una agencia tech argentina presentando el estado del mercado"

# Tip tecnico
elif content_type == "tip_tecnico":
    style = style
    image_style = image_style
    narration_tone = narration_tone

# Caso de uso
elif content_type == "caso_uso":
    style = style
    image_style = image_style
    narration_tone = narration_tone

# Educativo
elif content_type == "educativo":
    style = style
    image_style = image_style
    narration_tone = narration_tone

# Promocion
elif content_type == "promocion":
    style = style
    image_style = image_style
    narration_tone = narration_tone

# Fetch real GitHub context (non-blocking, fails silently)
github_ctx = fetch_github_context()


def call_api(endpoint, payload):
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        f"https://openrouter.ai/api/v1/{endpoint}",
        data=data,
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://tecnodespegue.com"
        }
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def text_from_msg(msg):
    return (msg.get("content") or "").strip()


def clean_text(text):
    """Elimina markdown que no renderiza bien en redes sociales"""
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'_+', '', text)
    text = re.sub(r'`+', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def upload_to_postiz(file_path):
    result = subprocess.run(
        [POSTIZ_BIN, "upload", file_path],
        capture_output=True, text=True, env=ENV
    )
    if result.returncode != 0:
        raise ValueError(f"upload failed: {result.stderr}")
    output = result.stdout.strip()
    # Strategy 1: extract URL directly from known JSON key (works with emoji/text prefix)
    key_match = re.search(r'"(?:path|url|file_url|download_url|src)"\s*:\s*"(https://[^"]+)"', output)
    if key_match:
        return key_match.group(1)
    # Strategy 2: extract any https:// URL, excluding JSON/shell punctuation
    url_match = re.search(r'https://[^\s"\'<>{}|\\^`\[\]]+', output)
    if url_match:
        return url_match.group(0).rstrip(".,;:")
    raise ValueError(f"No se pudo extraer URL del upload. Output: {output[:200]}")


def generate_tts(text, out_path):
    result = subprocess.run(
        ["python3", "-m", "edge_tts", "--voice", TTS_VOICE, "--text", text, "--write-media", out_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise ValueError(f"edge-tts error: {result.stderr}")


def create_reel_video(img_path, audio_path, out_path):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-i", audio_path,
        "-filter_complex",
        (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=20:5[bg];"
            "[0:v]scale=1080:1080,"
            "zoompan=z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            ":d=9999:s=1080x1080[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2[out]"
        ),
        "-map", "[out]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        out_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(out_path) or os.path.getsize(out_path) < 10000:
        raise ValueError(f"ffmpeg no genero video valido: {result.stderr[-400:]}")


def post_to_discord(content_type, post_text, media_url=None):
    channel_id = DISCORD_CHANNELS.get(content_type)
    if not channel_id:
        return
    labels = {
        "tip_tecnico": "Tip Tecnico",
        "caso_uso":    "Caso de Uso",
        "educativo":   "Educativo",
        "promocion":   "Promocion",
        "tutorial_programacion": "Tutorial",
        "tech_news_2026": "Noticias Tech"
    }
    label = labels.get(content_type, "Post")
    msg = f"**{label}**\\n\\n{post_text[:500]}"
    if media_url:
        msg += f"\\n\\n{media_url}"

    payload = json.dumps({"content": msg[:2000]}).encode()
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        data=payload,
        headers={
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://tecnodespegue.com, 1.0)"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"Discord: publicado en {content_type} (HTTP {resp.status})")
    except urllib.error.HTTPError as e:
        print(f"Discord error: {e.code} {e.read().decode()[:200]}")


def save_to_obsidian(content_type, post_text, media_url=None):
    labels = {
        "tip_tecnico": "Tip Tecnico",
        "caso_uso":    "Caso de Uso",
        "educativo":   "Educativo",
        "promocion":   "Promocion",
        "tutorial_programacion": "Tutorial",
        "tech_news_2026": "Noticias Tech"
    }
    label = labels.get(content_type, "Post")
    fecha = ARG_NOW.strftime("%Y-%m-%d")
    hora  = ARG_NOW.strftime("%H:%M")
    fname = f"{fecha} {hora} {label}.md"
    folder = os.path.join(OBSIDIAN_VAULT, "Social Media")
    os.makedirs(folder, exist_ok=True)
    media_line = f"\\n**Media**: {media_url}" if media_url else ""
    note = (
        f"---\\ntags: [post, {content_type}, tecnodespegue]\\n"
        f"fecha: {fecha}\\nhora: {hora}\\ntipo: {label}\\n---\\n\\n"
        f"# {label} - {fecha} {hora}\\n{media_line}\\n\\n"
        f"## Contenido publicado\\n\\n{post_text}\\n\\n"
        f"---\\n*Publicado automaticamente por Tecno Squire*\\n"
    )
    with open(os.path.join(folder, fname), "w") as f:
        f.write(note)
    print(f"Obsidian: guardado Social Media/{fname}")


# ─── 1. TEXTO ─────────────────────────────────────────────────────────────
print(f"[{content_type}] Generando texto profesional...")

# Fetch trending context
trends_ctx = ""
trending_topic = None
try:
    from trending import get_trending_context, select_trending_topic
    trends_ctx = get_trending_context()
    if trends_ctx:
        trending_topic = select_trending_topic(trends_ctx, content_type, OPENROUTER_KEY)
except Exception as e:
    print(f"  Trending unavailable: {e}")

# Use multi-agent pipeline if available
_multiagent_ok = False
try:
    from crew import generate_post_multiagent
    _style_with_topic = style
    if topic:
        _style_with_topic = "Tema: " + str(topic) + "\n\n" + style
    if trending_topic:
        _style_with_topic = "TRENDING TOPIC DE HOY: " + str(trending_topic) + "\n\n" + _style_with_topic
    
    post_text = generate_post_multiagent(
        OPENROUTER_KEY, content_type, _style_with_topic, AGENCY_CONTEXT,
        trends_ctx=trends_ctx, github_ctx=github_ctx or ""
    )
    post_text = clean_text(post_text)
    _multiagent_ok = True
    print(f"  [Multi-agente] Texto final: {len(post_text.split())} palabras")
except Exception as e:
    print(f"  Multi-agente fallo ({e}), usando pipeline simple...")

if not _multiagent_ok:
    _user_prompt = style
    if github_ctx:
        _gh_section = (
            "TRABAJO REAL DE TECNODESPEGUE:\n" + github_ctx +
            "\n\nUSO DE ESTE CONTEXTO: si hay un proyecto relevante mencionado arriba, "
            "usalo como ejemplo concreto de lo que TecnoDespegue construye para clientes. "
            "No menciones nombres tecnicos internos ni repos. "
            "Transformalo en lenguaje de negocio: 'construimos un sistema de X para una empresa de Y sector'. "
            "Esto hace el post autentico y especifico, no generico.\n\n"
        )
        _topic_extra = ("Enfoque del post: " + str(topic) + "\n\n") if topic else ""
        _user_prompt = _gh_section + _topic_extra + style
    elif topic:
        _user_prompt = "Tema: " + str(topic) + "\n\n" + style

    text_data = call_api("chat/completions", {
        "model": COPY_MODEL,
        "messages": [
            {"role": "system", "content": AGENCY_CONTEXT},
            {"role": "user",   "content": _user_prompt + "\n\nResponde SOLO con el texto del post. Sin markdown, sin asteriscos, sin titulos. Minimo 120 palabras, maximo 180."}
        ],
        "max_tokens": 600
    })
    post_text = clean_text(text_from_msg(text_data["choices"][0]["message"]))

if not post_text or len(post_text.split()) < 20:
    raise ValueError(f"Modelo no genero texto suficiente: {post_text[:50]!r}")
print(f"Texto ({len(post_text.split())} palabras): {post_text[:100]}...")

# ─── 2. TÍTULO YOUTUBE ────────────────────────────────────────────────────
first_line = post_text.split("\\n")[0].strip()
first_line = re.sub(r"#\\w+", "", first_line).strip()
if len(first_line) >= 10:
    words = first_line.split()
    yt_title = (" ".join(words)[:60] + " | TecnoDespegue").strip()
else:
    yt_title = "TecnoDespegue - Automatizacion y Desarrollo de Software"
yt_title = yt_title[:75]
print(f"Titulo YT: {yt_title}")

# ─── 3. NARRACIÓN ─────────────────────────────────────────────────────────
print("Generando narracion...")
narr_data = call_api("chat/completions", {
    "model": COPY_MODEL,
    "messages": [
        {"role": "system", "content": f"Sos locutor argentino, {narration_tone}. Solo texto hablado, sin hashtags, sin emojis, sin markdown, sin asteriscos. NO incluyas numeros de telefono. Solo mencioná el sitio web."},
        {"role": "user",   "content": f"Reescribi esto como locucion de 35-45 palabras para un Reel. NO incluyas numeros de telefono. Solo mencioná el sitio web.:\\n\\n{post_text}"}
    ],
    "max_tokens": 200
})
narration = clean_text(text_from_msg(narr_data["choices"][0]["message"]))
if not narration or len(narration) > 600:
    narration = " ".join(re.sub(r'#\w+', '', post_text).split()[:45])
print(f"Narracion ({len(narration.split())} palabras): {narration[:80]}...")

# ─── 4. IMAGEN FLUX ───────────────────────────────────────────────────────
print("Generando imagen FLUX.2 Klein...")
img_path = f"/tmp/tecno_img_{TS}.png"
try:
    img_data = call_api("chat/completions", {
        "model": IMAGE_MODEL,
        "messages": [{"role": "user", "content": (
            f"Professional social media image for TecnoDespegue, an Argentine tech agency. "
            f"Visual concept: {image_style}. "
            "Requirements: 4K quality, no text overlay, no watermarks, square format 1:1, "
            "commercial photography quality. Ultra detailed."
        )}],
        "max_tokens": 4096
    })
    flux_msg = img_data["choices"][0]["message"]
    raw_url  = ""
    images   = flux_msg.get("images")
    if isinstance(images, list) and images:
        raw_url = images[0].get("image_url", {}).get("url", "") or images[0].get("url", "")
    if not raw_url and isinstance(flux_msg.get("content"), list):
        for item in flux_msg["content"]:
            raw_url = item.get("image_url", {}).get("url", "") or item.get("url", "")
            if raw_url:
                break
    if raw_url.startswith("data:image"):
        _, b64data = raw_url.split(",", 1)
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(b64data))
    elif raw_url.startswith("http"):
        urllib.request.urlretrieve(raw_url, img_path)
    else:
        raise ValueError(f"FLUX formato inesperado: {raw_url[:80]!r}")
    print(f"Imagen: {img_path} ({os.path.getsize(img_path)//1024}KB)")
except Exception as e:
    print(f"Advertencia FLUX: {e}")
    img_path = None

# ─── 5. TTS + VIDEO ───────────────────────────────────────────────────────
audio_path = f"/tmp/tecno_audio_{TS}.mp3"
video_path = f"/tmp/tecno_reel_{TS}.mp4"
media_url  = None

try:
    print(f"TTS con {TTS_VOICE}...")
    generate_tts(narration, audio_path)
    print(f"Audio: {os.path.getsize(audio_path)//1024}KB")

    if img_path and os.path.exists(img_path):
        print("Creando video reel 9:16...")
        create_reel_video(img_path, audio_path, video_path)
        print(f"Video: {os.path.getsize(video_path)//1024}KB")
        media_url = upload_to_postiz(video_path)
        print(f"Subido: {media_url}")
    else:
        print("Sin imagen, publicando sin media...")
except Exception as e:
    print(f"Advertencia video/TTS: {e}")
    if img_path and os.path.exists(img_path):
        try:
            media_url = upload_to_postiz(img_path)
            print(f"Fallback imagen: {media_url}")
        except Exception as e2:
            print(f"Fallback fallido: {e2}")

# ─── 6. PUBLICAR ──────────────────────────────────────────────────────────
print("Publicando en redes...")
env_pub = {**ENV, "PATH": f"{NPM_BIN}:{os.environ.get('PATH', '')}"}
cmd_args = ["python3", PUBLISH_SCRIPT, "all", post_text, media_url or "", yt_title, "reel"]
result = subprocess.run(cmd_args, capture_output=True, text=True, env=env_pub)
print(result.stdout)
if result.returncode != 0:
    print(f"Error postiz: {result.stderr}", file=sys.stderr)

# ─── 7. DISCORD ───────────────────────────────────────────────────────────
print("Publicando en Discord...")
post_to_discord(content_type, post_text, media_url)

# ─── 8. OBSIDIAN ──────────────────────────────────────────────────────────
print("Guardando en Obsidian...")
try:
    save_to_obsidian(content_type, post_text, media_url)
except Exception as e:
    print(f"Advertencia Obsidian: {e}")

# Files kept for manual publishing
print("Video disponible en: " + video_path)
print("Pipeline completo.")
