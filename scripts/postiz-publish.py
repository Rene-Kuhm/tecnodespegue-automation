#!/usr/bin/env python3
"""Publicador multi-plataforma para TecnoDespegue via Postiz CLI"""
import subprocess, sys, os, json, re
from datetime import datetime, timezone, timedelta

POSTIZ_KEY = os.environ.get("POSTIZ_API_KEY", "")
NPM_BIN    = "/home/node/.npm-global/bin"
POSTIZ_BIN = f"{NPM_BIN}/postiz"
ENV = {**os.environ, "POSTIZ_API_KEY": POSTIZ_KEY, "PATH": f"{NPM_BIN}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"}

INTEGRATIONS = {
    "instagram": "cmni2kulq0772ql0yg5kg72zi",
    "facebook":  "cmnhl37kl053gpn0yxb2169oz",
    "tiktok":    "cmnhl4uu80595ql0y9s1j5g5n",
    "youtube":   "cmnhl3v54053kpn0yd5nzu422",
}

def get_settings(platform, content, yt_title=None, is_reel=False, media_url=None):
    if platform == "instagram":
        return {"post_type": "post"}
    
    if platform == "tiktok":
        # All these fields are REQUIRED by TikTok
        return {
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "duet": False,
            "stitch": False,
            "comment": True,
            "autoAddMusic": "no",
            "brand_content_toggle": False,
            "brand_organic_toggle": False,
            "content_posting_method": "UPLOAD"
        }
    
    if platform == "youtube":
        title = yt_title or re.sub(r'[^\w\s\-.,!?áéíóúñü]', '', re.sub(r'#\w+', '', content), flags=re.UNICODE)
        title = ' '.join(title.split())[:80].rstrip('.,!? ') or "TecnoDespegue - IA y Desarrollo Web"
        return {"title": title, "type": "public", "selfDeclaredMadeForKids": "no"}
    
    return None

MEDIA_REQUIRED_PLATFORMS = {"instagram", "tiktok", "youtube"}

def publish(platform, content, media_url=None, yt_title=None, schedule_offset_min=0, is_reel=False):
    if platform in MEDIA_REQUIRED_PLATFORMS and not media_url:
        print(f"  ⏭️  {platform}: requiere media, saltando")
        return False
    schedule = (datetime.now(timezone.utc) + timedelta(minutes=schedule_offset_min)).strftime("%Y-%m-%dT%H:%M:%SZ")
    cmd = [POSTIZ_BIN, "posts:create", "-c", content, "-s", schedule, "-i", INTEGRATIONS[platform]]
    if media_url:
        cmd += ["-m", media_url]
    settings = get_settings(platform, content, yt_title, is_reel, media_url)
    if settings:
        cmd += ["--settings", json.dumps(settings)]

    result = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
    output = result.stdout.strip()
    if result.returncode != 0 or "Error" in output:
        print(f"  ❌ {platform}: {output[:120] or result.stderr.strip()[:120]}")
        return False
    print(f"  ✅ {platform} → {schedule}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: postiz-publish.py [instagram|facebook|tiktok|youtube|all] 'contenido' [media_url] [yt_title]")
        sys.exit(1)

    platform  = sys.argv[1]
    content   = sys.argv[2]
    media_url = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
    yt_title  = sys.argv[4] if len(sys.argv) > 4 else None
    is_reel   = sys.argv[5].lower() == "reel" if len(sys.argv) > 5 else False

    platforms = list(INTEGRATIONS.keys()) if platform == "all" else [platform]
    if not media_url:
        skipped = [p for p in platforms if p in MEDIA_REQUIRED_PLATFORMS]
        platforms = [p for p in platforms if p not in MEDIA_REQUIRED_PLATFORMS]
        if skipped:
            msg = ", ".join(skipped)
            print(f"  ⚠️  Sin media, saltando: {msg}")

    ok = 0
    for p in platforms:
        if publish(p, content, media_url, yt_title, is_reel=is_reel):
            ok += 1
    print(f"\n{'✅' if ok == len(platforms) else '⚠️'} {ok}/{len(platforms)} plataformas OK")
