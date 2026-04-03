import os
#!/usr/bin/env python3
"""
Tecno Squire Bot — Gateway persistente
- Auto-asigna @Miembro cuando alguien se une al servidor
- Manda DM de bienvenida con link a #reglas
- Muestra status "Watching TecnoDespegue"
"""
import discord
from discord.ext import commands
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/home/node/clawd/logs/discord-bot.log"),
        logging.StreamHandler()
    ]
)

TOKEN        = "os.environ.get("DISCORD_TOKEN", "")"
GUILD_ID     = 1489363760375398480
MIEMBRO_ROLE = 1489378924705218631   # @Miembro
BIENVENIDA_CH = 1489378952916742154  # #👋-bienvenida (se detecta en on_ready)

intents = discord.Intents.default()
intents.members = True
intents.message_content = False

bot = discord.Client(intents=intents)

BIENVENIDA_ID = None
REGLAS_ID     = None

@bot.event
async def on_ready():
    global BIENVENIDA_ID, REGLAS_ID
    guild = bot.get_guild(GUILD_ID)
    for ch in guild.channels:
        if "bienvenida" in ch.name:
            BIENVENIDA_ID = ch.id
        if "reglas" in ch.name:
            REGLAS_ID = ch.id

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="TecnoDespegue 🚀"
        )
    )
    logging.info(f"Bot online — {guild.name} | bienvenida={BIENVENIDA_ID} reglas={REGLAS_ID}")

@bot.event
async def on_member_join(member):
    guild = member.guild
    logging.info(f"Nuevo miembro: {member} ({member.id})")

    # Asignar @Miembro automáticamente
    role = guild.get_role(MIEMBRO_ROLE)
    if role:
        try:
            await member.add_roles(role, reason="Auto-rol al unirse")
            logging.info(f"  Rol @Miembro asignado a {member}")
        except discord.Forbidden:
            logging.warning(f"  Sin permisos para asignar rol a {member}")

    # DM de bienvenida
    reglas_link = f"<#{REGLAS_ID}>" if REGLAS_ID else "#reglas"
    presentate_link = "<#1489378952916742154>"
    try:
        await member.send(
            f"👋 ¡Hola **{member.display_name}**!\n\n"
            f"Bienvenido/a a **TecnoDespegue** — la comunidad de dev web, automatización e IA.\n\n"
            f"📋 Leé las reglas: {reglas_link}\n"
            f"🙋 Presentate en: <#1489378952916742154>\n"
            f"💬 Charlá en: <#1489363760375398483>\n\n"
            f"El contenido se publica automáticamente 4 veces al día. ¡Activá las notificaciones! 🔔"
        )
        logging.info(f"  DM enviado a {member}")
    except discord.Forbidden:
        logging.info(f"  {member} tiene DMs cerrados")

bot.run(TOKEN, log_handler=None)
