#!/bin/sh
# Peppa Box: Spotify-Ausgang umstellen (Lautsprecher <-> Kopfhoerer). Laeuft als root ueber die
# sudo-Freigabe aus dienst_einrichten.sh, installiert als /usr/local/sbin/peppa-ausgang (root-eigene
# Kopie, nicht die Datei im Repository).
#   peppa-ausgang zeigen          aktuelles Geraet aus /etc/raspotify/conf ausgeben
#   peppa-ausgang lautsprecher    LIBRESPOT_DEVICE="lautsprecher", Raspotify neu starten
#   peppa-ausgang kopfhoerer      LIBRESPOT_DEVICE="kopfhoerer",   Raspotify neu starten
# Ist das Geraet schon eingestellt, wird Raspotify trotzdem neu gestartet (der Player ruft nur auf,
# wenn er umschalten will, und wartet danach auf das Geraet).
CONF=/etc/raspotify/conf
ASOUND=/etc/asound.conf
SYSTEMCTL=systemctl
if [ -z "$SUDO_USER" ]; then      # nur fuer Tests ohne sudo: Pfade umlenken (ueber sudo nie)
    CONF="${PEPPA_RASPOTIFY:-$CONF}"
    ASOUND="${PEPPA_ASOUND:-$ASOUND}"
    SYSTEMCTL="${PEPPA_SYSTEMCTL:-$SYSTEMCTL}"
fi

case "$1" in
    zeigen)
        sed -n 's/^LIBRESPOT_DEVICE="\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' "$CONF" | tail -n 1
        exit 0 ;;
    lautsprecher|kopfhoerer) ZIEL="$1" ;;
    *)
        echo "Aufruf: peppa-ausgang zeigen|lautsprecher|kopfhoerer"
        exit 2 ;;
esac

if [ ! -f "$CONF" ]; then
    echo "Raspotify-Einstellungen ($CONF) fehlen."
    exit 3
fi
if ! grep -q "^pcm\.$ZIEL " "$ASOUND" 2> /dev/null; then
    echo "ALSA-Geraet '$ZIEL' fehlt in $ASOUND (lautsprecher_einrichten.sh ausfuehren)."
    exit 4
fi
if grep -q '^LIBRESPOT_DEVICE=' "$CONF"; then
    sed -i "s|^LIBRESPOT_DEVICE=.*|LIBRESPOT_DEVICE=\"$ZIEL\"|" "$CONF"
else
    echo "LIBRESPOT_DEVICE=\"$ZIEL\"" >> "$CONF"
fi
"$SYSTEMCTL" restart raspotify
echo "Spotify-Ausgang: $ZIEL"
