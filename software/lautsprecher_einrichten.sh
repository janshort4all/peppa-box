#!/bin/sh
# Richtet den Lautsprecher (MAX98357A ueber I2S) ein. Wird von dienst_einrichten.sh aufgerufen,
# kann aber auch allein laufen. Beliebig oft wiederholbar.
#   1. config.txt: I2S-Ausgang (hifiberry-dac) und GPIO 16 (SD/stumm) als Eingang ohne Pull
#   2. /etc/asound.conf: Software-Lautstaerke "lautsprecher" mit Regler "Lautsprecher"
#      (der MAX98357A hat keinen eigenen Regler, Spotify steht fest auf 100 %)
#   3. Raspotify gibt ueber "lautsprecher" aus
# Die Karte wird gesucht (Name mit "hifiberry" in /proc/asound/cards), nicht angenommen.
# Kopfhoerer-Umschaltung (Pin 37) kommt spaeter; bis dahin ist die Pi-Klinke stumm.
set -e
CFG="${PEPPA_CONFIG_TXT:-/boot/firmware/config.txt}"
ASOUND="${PEPPA_ASOUND:-/etc/asound.conf}"
RASPOTIFY="${PEPPA_RASPOTIFY:-/etc/raspotify/conf}"
KARTEN="${PEPPA_KARTEN:-/proc/asound/cards}"
NEUSTART=0

# --- 1. config.txt
zeile_sicherstellen() {   # $1 = Zeile, $2 = Anfang zum Erkennen
    if ! grep -q "^$2" "$CFG"; then
        echo "$1" | sudo tee -a "$CFG" > /dev/null
        echo "config.txt: '$1' ergaenzt."
        NEUSTART=1
    fi
}
LETZTER_ABSCHNITT="$(grep '^\[' "$CFG" | tail -n 1 || true)"
if [ -n "$LETZTER_ABSCHNITT" ] && [ "$LETZTER_ABSCHNITT" != "[all]" ]; then
    echo "config.txt endet nicht mit [all], sondern mit $LETZTER_ABSCHNITT. Lautsprecher NICHT eingerichtet."
    exit 1
fi
zeile_sicherstellen "dtoverlay=hifiberry-dac" "dtoverlay=hifiberry-dac"
zeile_sicherstellen "gpio=16=ip,pn" "gpio=16="
# Sofort wirksam, ohne Neustart (Stummschaltung loesen)
if command -v pinctrl > /dev/null; then sudo pinctrl set 16 ip pn || true; fi

# --- Karte suchen
KARTE="$(sed -n 's/^ *[0-9][0-9]* \[\([^] ]*\) *\]:.*[Hh][Ii][Ff][Ii][Bb][Ee][Rr][Rr][Yy].*/\1/p' "$KARTEN" | head -n 1)"
if [ -z "$KARTE" ]; then
    echo "Verstaerker-Karte (hifiberry) nicht gefunden."
    if [ "$NEUSTART" = 1 ]; then
        echo "Bitte neu starten (sudo reboot) und danach dieses Skript noch einmal ausfuehren."
    fi
    exit 0
fi
echo "Verstaerker-Karte: $KARTE"

# --- 2. Software-Lautstaerke in /etc/asound.conf (eigener Block zwischen Markierungen)
ANFANG="# >>> peppa-box lautsprecher"
ENDE="# <<< peppa-box lautsprecher"
TMP="$(mktemp)"
if [ -f "$ASOUND" ]; then
    sed "/^$ANFANG\$/,/^$ENDE\$/d" "$ASOUND" > "$TMP"
fi
cat >> "$TMP" <<EOF
$ANFANG
pcm.lautsprecher {
    type softvol
    slave.pcm "plughw:CARD=$KARTE,DEV=0"
    control {
        name "Lautsprecher"
        card $KARTE
    }
}
$ENDE
EOF
if [ -f "$ASOUND" ] && cmp -s "$TMP" "$ASOUND"; then
    rm -f "$TMP"
else
    sudo install -m 0644 -o root -g root "$TMP" "$ASOUND"
    rm -f "$TMP"
    echo "$ASOUND: Software-Lautstaerke eingetragen."
fi

# --- 3. Raspotify auf den Lautsprecher
if sudo test -f "$RASPOTIFY"; then   # Datei/Ordner nur mit sudo lesbar
    if sudo grep -q '^LIBRESPOT_DEVICE="lautsprecher"$' "$RASPOTIFY"; then
        :
    elif sudo grep -q '^LIBRESPOT_DEVICE=' "$RASPOTIFY"; then
        sudo sed -i 's|^LIBRESPOT_DEVICE=.*|LIBRESPOT_DEVICE="lautsprecher"|' "$RASPOTIFY"
        echo "Raspotify: Ausgabe auf Lautsprecher umgestellt."
    else
        echo 'LIBRESPOT_DEVICE="lautsprecher"' | sudo tee -a "$RASPOTIFY" > /dev/null
        echo "Raspotify: Ausgabe auf Lautsprecher eingetragen."
    fi
else
    echo "Raspotify-Einstellungen ($RASPOTIFY) nicht gefunden, Ausgabe nicht umgestellt."
fi

# --- Regler anlegen (entsteht erst beim ersten Abspielen) und beim ersten Mal leise stellen
if [ -z "$PEPPA_TROCKEN" ]; then
    sudo systemctl stop raspotify 2> /dev/null || true
    if ! sudo amixer -c "$KARTE" sget Lautsprecher > /dev/null 2>&1; then
        sudo aplay -q -D lautsprecher -d 1 -f S16_LE -r 44100 -c 2 /dev/zero || true
        sudo amixer -q -M -c "$KARTE" sset Lautsprecher 30% || true
        echo "Regler 'Lautsprecher' angelegt, auf 30 % gestellt."
    fi
    sudo alsactl store || true
    sudo systemctl start raspotify 2> /dev/null || true
fi

if [ "$NEUSTART" = 1 ]; then
    echo "config.txt wurde geaendert: Bitte einmal neu starten (sudo reboot)."
fi
