#!/bin/sh
# Richtet den Lautsprecher (MAX98357A ueber I2S) ein. Wird von dienst_einrichten.sh aufgerufen,
# kann aber auch allein laufen. Beliebig oft wiederholbar.
#   1. config.txt: I2S-Ausgang (hifiberry-dac); GPIO 16 (SD) beim Einschalten auf "stumm" (Ausgang low)
#   2. /etc/asound.conf: Mischer (dmix) -> Software-Lautstaerke "lautsprecher", Regler "Lautsprecher"
#      (der MAX98357A hat keinen eigenen Regler, Spotify steht fest auf 100 %)
#   3. Dienst peppa-stille: spielt dauerhaft Stille in den Mischer, damit der Takt nie abreisst und
#      der Verstaerker wach bleibt (sonst knackt es bei jedem Abspielbeginn). Reihenfolge gegen das
#      Knacken beim Ein-/Ausschalten: stumm -> Stille startet -> 0,5 s spaeter SD frei;
#      beim Stoppen erst stumm, dann Stille aus.
#   4. Raspotify gibt ueber "lautsprecher" aus und darf den Mischer mitbenutzen (kein eigenes IPC)
#   5. Kopfhoerer: eigener Mischer "kopfhoerer" auf der Pi-Klinke (Karte "Headphones"), damit Spotify
#      und Ansagen gleichzeitig spielen koennen. Umgeschaltet wird vom Player (Klinke an P26) ueber
#      /usr/local/sbin/peppa-ausgang; steht Raspotify schon auf "kopfhoerer", bleibt das so.
# Die Karten werden gesucht (Name mit "hifiberry" bzw. "Headphones" in /proc/asound/cards), nicht angenommen.
set -e
CFG="${PEPPA_CONFIG_TXT:-/boot/firmware/config.txt}"
ASOUND="${PEPPA_ASOUND:-/etc/asound.conf}"
RASPOTIFY="${PEPPA_RASPOTIFY:-/etc/raspotify/conf}"
KARTEN="${PEPPA_KARTEN:-/proc/asound/cards}"
SYSTEMD="${PEPPA_SYSTEMD:-/etc/systemd/system}"
BENUTZER="$(id -un)"
NEUSTART=0
SD_START="gpio=16=op,dl"        # beim Einschalten stumm; peppa-stille gibt SD frei

# --- 1. config.txt
zeile_sicherstellen() {   # $1 = Zeile, $2 = Anfang zum Erkennen; vorhandene andere Fassung wird ersetzt
    if grep -q "^$1\$" "$CFG"; then
        return
    fi
    if grep -q "^$2" "$CFG"; then
        sudo sed -i "s|^$2.*|$1|" "$CFG"
        echo "config.txt: auf '$1' geaendert."
    else
        echo "$1" | sudo tee -a "$CFG" > /dev/null
        echo "config.txt: '$1' ergaenzt."
    fi
    NEUSTART=1
}
LETZTER_ABSCHNITT="$(grep '^\[' "$CFG" | tail -n 1 || true)"
if [ -n "$LETZTER_ABSCHNITT" ] && [ "$LETZTER_ABSCHNITT" != "[all]" ]; then
    echo "config.txt endet nicht mit [all], sondern mit $LETZTER_ABSCHNITT. Lautsprecher NICHT eingerichtet."
    exit 1
fi
zeile_sicherstellen "dtoverlay=hifiberry-dac" "dtoverlay=hifiberry-dac"
zeile_sicherstellen "$SD_START" "gpio=16="

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
KH_KARTE="$(sed -n 's/^ *[0-9][0-9]* \[\(Headphones\) *\]:.*/\1/p' "$KARTEN" | head -n 1)"

# --- 2. /etc/asound.conf (eigener Block zwischen Markierungen)
ANFANG="# >>> peppa-box lautsprecher"
ENDE="# <<< peppa-box lautsprecher"
TMP="$(mktemp)"
if [ -f "$ASOUND" ]; then
    sed "/^$ANFANG\$/,/^$ENDE\$/d" "$ASOUND" > "$TMP"
fi
cat >> "$TMP" <<EOF
$ANFANG
# Mischer: Stille (peppa-stille), Spotify und Ansagen teilen sich den Verstaerker.
# ipc_perm 0666, weil Raspotify unter einem eigenen Benutzer laeuft.
pcm.peppa_dmix {
    type dmix
    ipc_key 5150
    ipc_perm 0666
    slave {
        pcm "hw:CARD=$KARTE,DEV=0"
        rate 44100
        channels 2
        format S16_LE
        period_size 1024
        buffer_size 8192
    }
}
pcm.peppa_plug {
    type plug
    slave.pcm "peppa_dmix"
}
pcm.lautsprecher {
    type softvol
    slave.pcm "peppa_plug"
    control {
        name "Lautsprecher"
        card $KARTE
    }
}
EOF
if [ -n "$KH_KARTE" ]; then
    cat >> "$TMP" <<EOF
# Kopfhoerer (Pi-Klinke): Spotify und Ansagen mischen; Lautstaerke ueber den Regler PCM der Karte
pcm.peppa_kh_dmix {
    type dmix
    ipc_key 5151
    ipc_perm 0666
    slave {
        pcm "hw:CARD=$KH_KARTE,DEV=0"
        rate 44100
        channels 2
        format S16_LE
        period_size 1024
        buffer_size 8192
    }
}
pcm.kopfhoerer {
    type plug
    slave.pcm "peppa_kh_dmix"
}
EOF
else
    echo "Kopfhoerer-Karte (Headphones) nicht gefunden: dtparam=audio=on in config.txt? Kopfhoerer-Ausgang fehlt."
fi
echo "$ENDE" >> "$TMP"
ASOUND_NEU=0
if [ -f "$ASOUND" ] && cmp -s "$TMP" "$ASOUND"; then
    rm -f "$TMP"
else
    sudo install -m 0644 -o root -g root "$TMP" "$ASOUND"
    rm -f "$TMP"
    ASOUND_NEU=1
    echo "$ASOUND: Mischer und Software-Lautstaerke eingetragen."
fi

# --- 3. Dienst peppa-stille
PINCTRL="$(command -v pinctrl || echo /usr/bin/pinctrl)"
APLAY="$(command -v aplay || echo /usr/bin/aplay)"
TMP="$(mktemp)"
cat > "$TMP" <<EOF
# Peppa Box (erzeugt von lautsprecher_einrichten.sh): Verstaerker wach halten, gegen Knacken
[Unit]
Description=Peppa Box Verstaerker wach halten (Stille)
After=sound.target alsa-restore.service
Wants=sound.target
Before=raspotify.service peppa-player.service

[Service]
Type=simple
ExecStartPre=$PINCTRL set 16 op dl
ExecStart=$APLAY -q -D peppa_dmix -t raw -r 44100 -c 2 -f S16_LE /dev/zero
ExecStartPost=/bin/sh -c 'sleep 0.5; $PINCTRL set 16 ip pn'
ExecStop=$PINCTRL set 16 op dl
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF
DIENST_NEU=0
if [ -f "$SYSTEMD/peppa-stille.service" ] && cmp -s "$TMP" "$SYSTEMD/peppa-stille.service"; then
    rm -f "$TMP"
else
    sudo mkdir -p "$SYSTEMD"
    sudo install -m 0644 -o root -g root "$TMP" "$SYSTEMD/peppa-stille.service"
    rm -f "$TMP"
    DIENST_NEU=1
    echo "Dienst peppa-stille eingerichtet."
fi

# --- 4. Raspotify auf den Lautsprecher, Mischer mitbenutzen
if sudo test -f "$RASPOTIFY"; then   # Datei/Ordner nur mit sudo lesbar
    if sudo grep -q '^LIBRESPOT_DEVICE="\(lautsprecher\|kopfhoerer\)"$' "$RASPOTIFY"; then
        :                                    # kopfhoerer: vom Player umgeschaltet, so lassen
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
sudo mkdir -p "$SYSTEMD/raspotify.service.d"
TMP="$(mktemp)"
printf '%s\n' "# Peppa Box: Raspotify teilt sich den Mischer (dmix) mit peppa-stille" "[Service]" "PrivateIPC=no" > "$TMP"
sudo install -m 0644 -o root -g root "$TMP" "$SYSTEMD/raspotify.service.d/peppa-ipc.conf"
rm -f "$TMP"

# --- Dienste neu starten, Regler beim ersten Mal anlegen und leise stellen, Probe
if [ -z "$PEPPA_TROCKEN" ]; then
    sudo systemctl daemon-reload
    sudo systemctl stop raspotify 2> /dev/null || true
    sudo systemctl enable peppa-stille > /dev/null 2>&1
    if [ "$ASOUND_NEU" = 1 ] || [ "$DIENST_NEU" = 1 ] || ! systemctl is-active --quiet peppa-stille; then
        sudo systemctl restart peppa-stille
        sleep 1
    fi
    if ! sudo amixer -c "$KARTE" sget Lautsprecher > /dev/null 2>&1; then
        sudo aplay -q -D lautsprecher -d 1 -f S16_LE -r 44100 -c 2 /dev/zero || true
        sudo amixer -q -M -c "$KARTE" sset Lautsprecher 30% || true
        echo "Regler 'Lautsprecher' angelegt, auf 30 % gestellt."
    fi
    sudo alsactl store || true
    # Probe: ein zweites Programm muss neben der Stille abspielen koennen (wie spaeter Spotify)
    if systemctl is-active --quiet peppa-stille && \
            sudo -u "$BENUTZER" aplay -q -D lautsprecher -d 1 -f S16_LE -r 44100 -c 2 /dev/zero 2> /dev/null; then
        echo "Lautsprecher: Stille laeuft, Mischen klappt."
    else
        echo "WARNUNG: peppa-stille oder Mischer arbeitet nicht. Bitte 'journalctl -u peppa-stille -n 20' ansehen."
    fi
    sudo systemctl start raspotify 2> /dev/null || true
fi

if [ "$NEUSTART" = 1 ]; then
    echo "config.txt wurde geaendert: Bitte einmal neu starten (sudo reboot)."
fi
