#!/bin/bash
: ${POSTIZ_API_KEY:?"ERROR: POSTIZ_API_KEY no configurada"}
export PATH="/home/node/.npm-global/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
INSTAGRAM="cmnhl2fg5058nql0ywse1qtqp"
FACEBOOK="cmnhl37kl053gpn0yxb2169oz"
TIKTOK="cmnhl4uu80595ql0y9s1j5g5n"
YOUTUBE="cmnhl3v54053kpn0yd5nzu422"
TIKTOK_SETTINGS='{"privacy_level":"PUBLIC_TO_EVERYONE","duet":true,"stitch":true,"comment":true,"autoAddMusic":"no","brand_content_toggle":false,"brand_organic_toggle":false,"content_posting_method":"DIRECT_POST"}'
INSTAGRAM_SETTINGS='{"post_type":"post"}'
PLATFORM=$1
CONTENT=$2
SCHEDULE=${3:-$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+5M +"%Y-%m-%dT%H:%M:%SZ")}
IMAGE_URL=$4
build_cmd() {
  local id=$1
  local settings=$2
  local cmd="postiz posts:create -c "$CONTENT" -s "$SCHEDULE" -i "$id""
  [ -n "$IMAGE_URL" ] && cmd="$cmd -m "$IMAGE_URL""
  [ -n "$settings" ] && cmd="$cmd --settings '$settings'"
  echo "$cmd"
}
case $PLATFORM in
  instagram)
    if [ -z "$IMAGE_URL" ]; then echo "⏭️ Instagram requiere media"; exit 1; fi
    eval $(build_cmd "$INSTAGRAM" "$INSTAGRAM_SETTINGS")
    ;;
  facebook)
    eval $(build_cmd "$FACEBOOK" "")
    ;;
  tiktok)
    if [ -z "$IMAGE_URL" ]; then echo "⏭️ TikTok requiere media"; exit 1; fi
    eval $(build_cmd "$TIKTOK" "$TIKTOK_SETTINGS")
    ;;
  youtube)
    eval $(build_cmd "$YOUTUBE" "")
    ;;
  all)
    if [ -n "$IMAGE_URL" ]; then
      eval $(build_cmd "$INSTAGRAM" "$INSTAGRAM_SETTINGS")
      eval $(build_cmd "$TIKTOK" "$TIKTOK_SETTINGS")
    else
      echo "⚠️ Sin media, saltando Instagram y TikTok"
    fi
    eval $(build_cmd "$FACEBOOK" "")
    echo "✅ Publicado para $SCHEDULE"
    exit 0
    ;;
  *) echo "Uso: postiz-publish.sh [instagram|facebook|tiktok|youtube|all] 'contenido' [fecha] [imagen_url]"; exit 1 ;;
esac
echo "✅ Publicado en $PLATFORM para $SCHEDULE"
