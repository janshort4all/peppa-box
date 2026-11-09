#!/bin/sh
# Richtet den Lautsprecher (MAX98357A ueber I2S) ein. Wird von dienst_einrichten.sh aufgerufen,
# kann aber auch allein laufen. Beliebig oft wiederholbar.
#   1. config.txt: I2S-Ausgang (hifiberry-dac); GPIO 16 (SD) beim Einschalten auf "stumm" (Ausgang low)
#   2. /etc/asound.conf: Mischer (dmix) -> Software-Lautstaerke "lautsprecher", Regler "Lautsprecher",
#      dazwischen der Equalizer "peppa_klang" (Klang auf der Eltern-Seite), wenn er nachweislich laeuft
#      (der MAX98357A hat keinen eigenen Regler, Spotify steht fest auf 100 %)
#   3. Dienst peppa-stille: spielt dauerhaft Stille in den Mischer, damit der Takt nie abreisst und
#      der Verstaerker wach bleibt (sonst knackt es bei jedem Abspielbeginn). Reihenfolge gegen das
#      Knacken beim Ein-/Ausschalten: stumm -> Stille startet -> 0,5 s spaeter SD hoch (3,3 V, nicht offen: Befund 08.11.);
#      beim Stoppen erst stumm, dann Stille aus.
#   4. Raspotify gibt den Ton ueber die Tonausgabe der Box aus (/usr/local/lib/peppa-box/ausgabe =
#      ausgabe.py, librespot --backend subprocess): die spielt auf "lautsprecher" oder "kopfhoerer",
#      je nach Vorgabe des Players, und wechselt ohne Raspotify-Neustart (seit 09.11.2026).
#      Ereignisse von librespot gehen an den Player (/usr/local/lib/peppa-box/ereignis).
#      Ist die Tonausgabe nicht installiert oder PEPPA_ALSA_DIREKT=1 gesetzt (Notfall-Rueckweg):
#      direkt ueber ALSA auf "lautsprecher", dann ohne Kopfhoerer-Umschaltung.
#      Raspotify darf den Mischer mitbenutzen (kein eigenes IPC).
#   5. Kopfhoerer: eigener Mischer "kopfhoerer" auf der Pi-Klinke (Karte "Headphones"), damit Spotify
#      und Ansagen gleichzeitig spielen koennen.
# Die Karten werden gesucht (Name mit "hifiberry" bzw. "Headphones" in /proc/asound/cards), nicht angenommen.
set -e
CFG="${PEPPA_CONFIG_TXT:-/boot/firmware/config.txt}"
ASOUND="${PEPPA_ASOUND:-/etc/asound.conf}"
RASPOTIFY="${PEPPA_RASPOTIFY:-/etc/raspotify/conf}"
KARTEN="${PEPPA_KARTEN:-/proc/asound/cards}"
SYSTEMD="${PEPPA_SYSTEMD:-/etc/systemd/system}"
RELAIS="${PEPPA_RELAIS:-/usr/local/lib/peppa-box/ausgabe}"
EREIGNIS="${PEPPA_EREIGNIS:-/usr/local/lib/peppa-box/ereignis}"
BENUTZER="$(id -un)"
NEUSTART=0
SD_START="gpio=16=op,dl"        # beim Einschalten stumm; peppa-stille setzt SD danach hoch

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

# Befehl so ausfuehren, wie Raspotify laeuft (root ohne Rechte, eigener Benutzer-Namensraum,
# schreibgeschuetztes System, kein /home); ohne systemd-run einfach als root
wie_raspotify() {
    if ! command -v systemd-run > /dev/null; then
        sudo /bin/sh -c "$1" > /dev/null
        return
    fi
    sudo systemd-run --quiet --wait --pipe --collect \
        -p ProtectSystem=strict -p ProtectHome=true -p PrivateTmp=true -p PrivateUsers=true \
        -p ProtectProc=invisible -p ProcSubset=pid -p NoNewPrivileges=true -p MemoryDenyWriteExecute=true \
        -p LockPersonality=true -p RestrictRealtime=true -p RestrictNamespaces=true \
        -p "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_NETLINK" -p SystemCallArchitectures=native \
        -p SystemCallFilter=@system-service -p "SystemCallFilter=~@privileged @resources" \
        -p SystemCallErrorNumber=EPERM -p DevicePolicy=strict -p "DeviceAllow=char-alsa rw" \
        -p "DeviceAllow=/dev/null rw" -p SupplementaryGroups=audio -p CapabilityBoundingSet= \
        /bin/sh -c "$1" > /dev/null
}

# 1 s Stille als Datei fuer die Proben: Raspotify (und damit die Probe) darf /dev/zero nicht oeffnen
# (DevicePolicy=strict, erlaubt sind nur Soundgeraete und /dev/null; Befund 09.11.2026)
STILLE=/run/peppa-box-stille.raw
if [ -z "$PEPPA_TROCKEN" ]; then
    head -c 176400 /dev/zero | sudo tee "$STILLE" > /dev/null
    sudo chmod 0644 "$STILLE"
fi

# --- Equalizer (Klang, Eltern-Seite): alsaequal + LADSPA-Modul Eq10 (Pakete libasound2-plugin-equal, caps).
#     Nur einbauen, wenn er unter den Schutzregeln von Raspotify nachweislich laeuft; sonst ohne.
EQ=0
if [ -n "$PEPPA_EQ" ]; then                  # nur Tests: 1 = vorhanden, 0 = nicht
    EQ="$PEPPA_EQ"
elif [ -z "$PEPPA_TROCKEN" ]; then
    if ! ls /usr/lib/*/alsa-lib/libasound_module_pcm_equal.so > /dev/null 2>&1; then
        echo "Installiere Equalizer (libasound2-plugin-equal, caps) ..."
        sudo apt-get install -y --no-install-recommends libasound2-plugin-equal > /dev/null 2>&1 \
            || { sudo apt-get update > /dev/null 2>&1 && \
                 sudo apt-get install -y --no-install-recommends libasound2-plugin-equal > /dev/null 2>&1; } \
            || echo "Equalizer nicht installiert (Klang-Einstellung fehlt dann)."
    fi
    if ls /usr/lib/*/alsa-lib/libasound_module_pcm_equal.so > /dev/null 2>&1; then
        PROBE="$(mktemp -d)"
        { cat /usr/share/alsa/alsa.conf
          echo 'pcm.peppa_probe_null { type null }'
          echo 'pcm.peppa_probe { type equal slave.pcm "peppa_probe_null" controls "/dev/shm/peppa-box-klang-probe.bin" }'
        } > "$PROBE/alsa.conf"
        chmod 0755 "$PROBE"; chmod 0644 "$PROBE/alsa.conf"
        sudo cp "$PROBE/alsa.conf" /run/peppa-box-klang-probe.conf
        if wie_raspotify "ALSA_CONFIG_PATH=/run/peppa-box-klang-probe.conf timeout 10 aplay -q -D plug:peppa_probe -t raw -f S16_LE -r 44100 -c 2 $STILLE"; then
            EQ=1
        else
            echo "WARNUNG: Equalizer laeuft unter den Schutzregeln von Raspotify nicht – Lautsprecher ohne Equalizer."
        fi
        sudo rm -f /run/peppa-box-klang-probe.conf /dev/shm/peppa-box-klang-probe.bin
        rm -rf "$PROBE"
    fi
fi
KLANG_DATEI=/dev/shm/peppa-box-klang.bin

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
EOF
if [ "$EQ" = 1 ]; then
    MONO_ZIEL="peppa_klang_plug"; MONO_ANTEIL="0.25"     # 6 dB Reserve: Equalizer hebt in Mittelstellung ca. 3 dB
else
    MONO_ZIEL="peppa_plug"; MONO_ANTEIL="0.5"
fi
cat >> "$TMP" <<EOF
# SD liegt fest auf 3,3 V = Verstaerker spielt den linken Kanal. Darum hier L+R gemischt auf beide Kanaele.
pcm.peppa_mono {
    type route
    slave.pcm "$MONO_ZIEL"
    slave.channels 2
    ttable.0.0 $MONO_ANTEIL
    ttable.1.0 $MONO_ANTEIL
    ttable.0.1 $MONO_ANTEIL
    ttable.1.1 $MONO_ANTEIL
}
pcm.peppa_mono_plug {
    type plug
    slave.pcm "peppa_mono"
}
EOF
if [ "$EQ" = 1 ]; then
    cat >> "$TMP" <<EOF
# Klang: Equalizer 10 Baender (Eltern-Seite, klang.py); Werte im Arbeitsspeicher, Raspotify darf lesen
pcm.peppa_klang_plug {
    type plug
    slave.pcm "peppa_klang"
}
pcm.peppa_klang {
    type equal
    slave.pcm "peppa_plug"
    controls "$KLANG_DATEI"
}
ctl.peppa_klang {
    type equal
    controls "$KLANG_DATEI"
}
EOF
fi
cat >> "$TMP" <<EOF
pcm.lautsprecher {
    type softvol
    slave.pcm "peppa_mono_plug"
    control {
        name "Lautsprecher"
        card $KARTE
    }
}
EOF
if [ -n "$KH_KARTE" ]; then
    cat >> "$TMP" <<EOF
# Kopfhoerer (Pi-Klinke) direkt, ohne Mischer: dmix oeffnet die Pi-Klinke zwar, gibt aber nie Ton aus
# (haengt; am Pi gemessen 09.11.2026). Lautstaerke ueber den Regler PCM der Karte.
pcm.kopfhoerer {
    type plug
    slave.pcm "hw:CARD=$KH_KARTE,DEV=0"
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

# --- Probe der ganzen Kette mit Equalizer (die Probe oben prueft ihn nur allein, gegen "null").
#     Am Pi (09.11.) brach aplay in der Kette mit Mischer ab (snd_pcm_hw_param_get_min: Assertion
#     !snd_interval_empty) -> kein Ton. Dann die Einrichtung ohne Equalizer wiederholen.
if [ "$EQ" = 1 ] && [ -z "$PEPPA_EQ" ] && [ -z "$PEPPA_TROCKEN" ]; then
    if ! sudo timeout 10 aplay -q -D lautsprecher -t raw -f S16_LE -r 44100 -c 2 "$STILLE" > /dev/null 2>&1; then
        echo "WARNUNG: Lautsprecher-Kette mit Equalizer spielt nicht – richte ohne Equalizer ein."
        PEPPA_EQ=0 exec sh "$0" "$@"
    fi
fi

# --- 3. Dienst peppa-stille
PINCTRL="$(command -v pinctrl || echo /usr/bin/pinctrl)"
KLANG_START=""
if [ "$EQ" = 1 ]; then   # Equalizer-Werte anlegen (root), dann fuer Player/Eltern-Seite beschreibbar
    AMIXER="$(command -v amixer || echo /usr/bin/amixer)"
    KLANG_START="ExecStartPre=-/bin/sh -c '$AMIXER -q -D peppa_klang controls > /dev/null 2>&1; chmod 0666 $KLANG_DATEI'"
fi
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
$KLANG_START
ExecStart=$APLAY -q -D peppa_dmix -t raw -r 44100 -c 2 -f S16_LE /dev/zero
ExecStartPost=/bin/sh -c 'sleep 0.5; $PINCTRL set 16 op dh'
ExecStop=$PINCTRL set 16 op dl
Restart=always
RestartSec=2
# aplay endet beim gewollten Stoppen mit 1 ("Interrupted system call"): kein Fehler
SuccessExitStatus=1

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

# --- 4. Raspotify: Ton ueber die Tonausgabe der Box, Ereignisse an den Player, Mischer mitbenutzen
raspotify_setzen() {   # $1 = Name, $2 = Wert; vorhandene Zeile ersetzen, sonst anhaengen (Kommentare bleiben)
    if sudo grep -q "^$1=" "$RASPOTIFY"; then
        sudo sed -i "s|^$1=.*|$1=\"$2\"|" "$RASPOTIFY"
    else
        echo "$1=\"$2\"" | sudo tee -a "$RASPOTIFY" > /dev/null
    fi
}
relais_pruefen() {   # 1 s Stille durch die Tonausgabe, mit denselben Schutzregeln wie der Raspotify-Dienst
    if [ -n "$PEPPA_RELAIS_PRUEFUNG" ]; then sh -c "$PEPPA_RELAIS_PRUEFUNG"; return; fi   # nur Tests
    if [ -n "$PEPPA_TROCKEN" ]; then return 0; fi
    wie_raspotify "$RELAIS < $STILLE"
}
if sudo test -f "$RASPOTIFY"; then   # Datei/Ordner nur mit sudo lesbar
    RELAIS_OK=0
    if [ -z "$PEPPA_ALSA_DIREKT" ] && [ -x "$RELAIS" ]; then
        if relais_pruefen; then
            RELAIS_OK=1
        else
            echo "WARNUNG: Probe der Tonausgabe ($RELAIS) fehlgeschlagen (Meldungen oben)."
            echo "         Raspotify spielt deshalb weiter direkt ueber ALSA, ohne Kopfhoerer-Umschaltung."
        fi
    fi
    if [ "$RELAIS_OK" = 1 ]; then
        raspotify_setzen LIBRESPOT_BACKEND subprocess
        raspotify_setzen LIBRESPOT_DEVICE "$RELAIS"
        echo "Raspotify: Ton ueber die Tonausgabe der Box (Kopfhoerer ohne Neustart)."
    else
        raspotify_setzen LIBRESPOT_BACKEND alsa
        raspotify_setzen LIBRESPOT_DEVICE lautsprecher
        echo "Raspotify: Ton direkt ueber ALSA auf den Lautsprecher (ohne Kopfhoerer-Umschaltung)."
    fi
    if [ -x "$EREIGNIS" ]; then
        raspotify_setzen LIBRESPOT_ONEVENT "$EREIGNIS"
    fi
else
    echo "Raspotify-Einstellungen ($RASPOTIFY) nicht gefunden, Ausgabe nicht umgestellt."
fi
[ -n "$PEPPA_TROCKEN" ] || sudo rm -f "$STILLE"
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
