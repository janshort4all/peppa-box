#!/bin/sh
# Peppa Box: Root-Helfer fuer den Ton. Laeuft als root ueber die sudo-Freigabe aus
# dienst_einrichten.sh, installiert als /usr/local/sbin/peppa-ausgang (root-eigene Kopie, nicht die
# Datei im Repository).
#   peppa-ausgang zeigen          "relais", wenn Raspotify ueber die Tonausgabe der Box spielt
#                                 (ausgabe.py: Kopfhoerer/Lautsprecher wechseln ohne Neustart);
#                                 sonst das ALSA-Geraet aus /etc/raspotify/conf (alter Weg)
#   peppa-ausgang neustart        Ton neu: Raspotify anhalten, peppa-stille (Mischer, Verstaerker)
#                                 neu starten, Raspotify starten
#   peppa-ausgang lautsprecher    alter Weg: LIBRESPOT_DEVICE="lautsprecher", Raspotify neu starten
#   peppa-ausgang kopfhoerer      alter Weg: LIBRESPOT_DEVICE="kopfhoerer",   Raspotify neu starten
#                                 (mit der Tonausgabe tun beide nichts: der Player wechselt selbst)
CONF=/etc/raspotify/conf
ASOUND=/etc/asound.conf
SYSTEMCTL=systemctl
RELAIS=/usr/local/lib/peppa-box/ausgabe
if [ -z "$SUDO_USER" ]; then      # nur fuer Tests ohne sudo: Pfade umlenken (ueber sudo nie)
    CONF="${PEPPA_RASPOTIFY:-$CONF}"
    ASOUND="${PEPPA_ASOUND:-$ASOUND}"
    SYSTEMCTL="${PEPPA_SYSTEMCTL:-$SYSTEMCTL}"
fi

relais() {
    grep -q '^LIBRESPOT_BACKEND="\{0,1\}subprocess"\{0,1\}$' "$CONF" 2> /dev/null &&
        grep -q "^LIBRESPOT_DEVICE=\"\{0,1\}$RELAIS\"\{0,1\}\$" "$CONF" 2> /dev/null
}

case "$1" in
    zeigen)
        if relais; then
            echo relais
        else
            sed -n 's/^LIBRESPOT_DEVICE="\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' "$CONF" | tail -n 1
        fi
        exit 0 ;;
    neustart)
        "$SYSTEMCTL" stop raspotify
        "$SYSTEMCTL" restart peppa-stille || echo "peppa-stille liess sich nicht neu starten."
        if "$SYSTEMCTL" start raspotify; then
            echo "Ton neu gestartet (Raspotify, peppa-stille)."
            exit 0
        fi
        echo "Raspotify startet nicht."
        exit 5 ;;
    lautsprecher|kopfhoerer) ZIEL="$1" ;;
    *)
        echo "Aufruf: peppa-ausgang zeigen|neustart|lautsprecher|kopfhoerer"
        exit 2 ;;
esac

if [ ! -f "$CONF" ]; then
    echo "Raspotify-Einstellungen ($CONF) fehlen."
    exit 3
fi
if relais; then
    echo "Tonausgabe der Box aktiv: den Ausgang ($ZIEL) stellt der Player selbst um."
    exit 0
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
