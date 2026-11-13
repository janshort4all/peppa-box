#!/bin/sh
# Richtet die Dienste der Peppa Box ein. Beide starten beim Einschalten und nach Fehlern neu.
#   peppa-player  Karten lesen, Spotify steuern
#   peppa-web     Eltern-Seite (Zustand, Neustart, Ausschalten, Update), Port 80 und 8080
#   peppa-startton  Startton sofort nach dem Einschalten (ohne auf WLAN/Spotify zu warten)
#   peppa-standby / peppa-aufwachen  Sparzustand (Ein-Taste 2 s halten): WLAN aus, nur die Ein-Taste wacht
# Dazu: sudo-Freigabe nur fuer die Befehle, die die Eltern-Seite braucht (/etc/sudoers.d/peppa-box),
# und die Gruppen fuer Akku/Touch (i2c), Protokoll (adm), Stromversorgung (video), Lautstaerke (audio),
# Ein-Taste/Klinke/Verstaerker (gpio), Kartenleser (spi) und Drehknopf (input).
# Ausserdem den Lautsprecher (lautsprecher_einrichten.sh), die Bedienelemente in config.txt
# (bedienung_einrichten.sh), den Ton-Helfer (/usr/local/sbin/peppa-ausgang: zeigen, Ton-Neustart),
# die Tonausgabe fuer Raspotify (/usr/local/lib/peppa-box/ausgabe: Kopfhoerer ohne Raspotify-Neustart)
# und das Ereignis-Programm (/usr/local/lib/peppa-box/ereignis), ein Protokoll, das Neustarts
# uebersteht, den Hardware-Waechter des Pi (startet bei einem Systemhaenger neu), die Sprachausgabe
# fuer Ansagen ohne eigene Aufnahme (pico2wave) und: Raspotify startet erst mit Netz.
# Notfall-Rueckweg (Ton wieder direkt ueber ALSA, ohne Kopfhoerer-Umschaltung):
#   PEPPA_ALSA_DIREKT=1 sh ~/peppa-box/software/dienst_einrichten.sh
# Und: WLAN-Stromsparen aus (sonst nach einer Weile nicht mehr erreichbar), WLAN-Suche alle 10 s ohne
# Verbindung (peppa-wlan-suche, Handy-Hotspot wird schnell gefunden), Heim-WLAN gibt nie auf.
# Aufruf (als normaler Benutzer, nicht als root):  sh ~/peppa-box/software/dienst_einrichten.sh
# Kann beliebig oft wiederholt werden.
set -e
BENUTZER="$(id -un)"
ORDNER="$(cd "$(dirname "$0")" && pwd)"
SYSTEMCTL="$(command -v systemctl)"
SUCHE_NEU=0
if [ "$BENUTZER" = "root" ]; then
    echo "Bitte ohne sudo aufrufen, das Skript fragt selbst nach dem Passwort."; exit 1
fi

# --- Player
sudo tee /etc/systemd/system/peppa-player.service > /dev/null <<EOF
[Unit]
Description=Peppa Box Player (Karten, Spotify)
After=network-online.target raspotify.service
Wants=network-online.target
# nie aufgeben, egal wie oft er neu starten muss
StartLimitIntervalSec=0

[Service]
User=$BENUTZER
WorkingDirectory=$ORDNER
ExecStart=/usr/bin/python3 $ORDNER/peppa_player.py
Environment=PYTHONUNBUFFERED=1
Restart=always
RestartSec=3
# beim Ausschalten nicht 90 s warten, falls der Player haengt
TimeoutStopSec=10
# Waechter: meldet sich der Player 30 s nicht (haengende Schleife), startet systemd ihn neu
WatchdogSec=30
NotifyAccess=main

[Install]
WantedBy=multi-user.target
EOF

# --- WLAN-Stromsparen aus: sonst ist die Box nach einiger Zeit ohne Verkehr ueber WLAN nicht mehr
#     erreichbar (Eltern-Seite, SSH, peppabox.local), waehrend Spotify weiterlaeuft.
if [ -d /etc/NetworkManager/conf.d ]; then
    sudo tee /etc/NetworkManager/conf.d/peppa-wlan-stromsparen-aus.conf > /dev/null <<EOF
# Peppa Box (erzeugt von dienst_einrichten.sh): WLAN-Stromsparen aus (2 = aus)
[connection]
wifi.powersave = 2
EOF
    echo "WLAN-Stromsparen aus (dauerhaft ab dem naechsten Einschalten)."
fi
# Sofort wirksam, ohne die WLAN-Verbindung neu aufzubauen (eine SSH-Sitzung bleibt bestehen)
if command -v iw > /dev/null && [ -d /sys/class/net/wlan0 ]; then
    sudo iw dev wlan0 set power_save off 2> /dev/null || true
fi

# --- Rechnername festschreiben, dann cloud-init abschalten.
#     cloud-init braucht nur der allererste Start (Raspberry Pi Imager: WLAN, Benutzer, Name) und kostet
#     danach bei jedem Start ca. 4-5 s. Es hat aber den Namen bei jedem Start gesetzt: ohne Festschreiben
#     koennte die Box danach anders heissen (Vorsichtsmassnahme; die Nichterreichbarkeit am
#     02.11.2026 kam von Avahi, siehe unten).
#     Rueckgaengig: sudo rm /etc/cloud/cloud-init.disabled
NAME="$(hostname)"
case "$NAME" in
    ""|localhost|localhost.*|raspberrypi) NAME="peppabox" ;;
esac
if [ "$(cat /etc/hostname 2> /dev/null)" != "$NAME" ] || [ "$(hostname)" != "$NAME" ]; then
    sudo hostnamectl set-hostname "$NAME"
    echo "Rechnername festgeschrieben: $NAME"
fi
if grep -q '^127\.0\.1\.1' /etc/hosts; then
    if ! grep -q "^127\.0\.1\.1[[:space:]]\+$NAME\$" /etc/hosts; then
        sudo sed -i "s/^127\.0\.1\.1.*/127.0.1.1\t$NAME/" /etc/hosts
    fi
else
    printf '127.0.1.1\t%s\n' "$NAME" | sudo tee -a /etc/hosts > /dev/null
fi
# Avahi (Name peppabox.local): nur IPv4 und nur WLAN. Sonst haelt Avahi nach einem Neuaufbau der
# WLAN-Adresse (v. a. IPv6) seine eigene alte Meldung fuer ein fremdes Geraet und nennt sich
# "peppabox-2.local" -> Box unter peppabox.local nicht mehr erreichbar (02.11.2026).
AVAHI_CONF="${PEPPA_AVAHI_CONF:-/etc/avahi/avahi-daemon.conf}"
if [ -f "$AVAHI_CONF" ]; then
    VORHER="$(cat "$AVAHI_CONF")"
    sudo sed -i -e 's/^#\?use-ipv6=.*/use-ipv6=no/' \
                -e 's/^#\?allow-interfaces=.*/allow-interfaces=wlan0/' "$AVAHI_CONF"
    grep -q '^use-ipv6=' "$AVAHI_CONF" || sudo sed -i 's/^\[server\]$/[server]\nuse-ipv6=no/' "$AVAHI_CONF"
    grep -q '^allow-interfaces=' "$AVAHI_CONF" || sudo sed -i 's/^\[server\]$/[server]\nallow-interfaces=wlan0/' "$AVAHI_CONF"
    if [ "$VORHER" != "$(cat "$AVAHI_CONF")" ]; then
        echo "Avahi: nur IPv4 und WLAN (gegen Umbenennung in peppabox-2.local)."
    fi
fi
sudo systemctl restart avahi-daemon 2> /dev/null || true
if [ -d /etc/cloud ] && [ ! -f /etc/cloud/cloud-init.disabled ]; then
    sudo touch /etc/cloud/cloud-init.disabled
    echo "cloud-init abgeschaltet (schnellerer Start ab dem naechsten Einschalten)."
fi

# --- Startton: sofort nach dem Einschalten, sobald der Ton laeuft (peppa-stille), ohne auf WLAN, Spotify
#     oder den Player zu warten. Grund (10.11.2026): "bereit" kommt erst, wenn Spotify die Box kennt, bis dahin
#     passierte fuer das Kind nach dem Druck auf die Ein-Taste lange nichts. Spielt toene.py start:
#     erst die Startlautstaerke, dann ansagen/start.wav (sonst zwei kurze Toene).
sudo tee /etc/systemd/system/peppa-startton.service > /dev/null <<EOF
[Unit]
Description=Peppa Box Startton (sofort, ohne auf das Netz zu warten)
After=peppa-stille.service sound.target alsa-restore.service
Wants=peppa-stille.service

[Service]
Type=oneshot
User=$BENUTZER
WorkingDirectory=$ORDNER
ExecStart=/usr/bin/python3 $ORDNER/toene.py start
TimeoutStartSec=20

[Install]
WantedBy=multi-user.target
EOF

# --- Zeitfresser beim Start abschalten: apt-daily und apt-daily-upgrade liefen bei jedem Einschalten (die Box
#     ist meist aus, die Zeitgeber holen es dann nach) und brauchten am Pi 3A+ zusammen ca. 9 s (Messung
#     10.11.2026), man-db und dpkg-db-backup nochmal ca. 2 s. Die Box aktualisiert sich dann nicht von selbst:
#     Betriebssystem-Updates von Hand (sudo apt update && sudo apt upgrade), Programm-Updates ueber die
#     Eltern-Seite. Rueckgaengig: sudo systemctl enable --now <name>.timer
for T in apt-daily.timer apt-daily-upgrade.timer man-db.timer dpkg-db-backup.timer; do
    if systemctl cat "$T" > /dev/null 2>&1 && systemctl is-enabled "$T" > /dev/null 2>&1; then
        sudo systemctl disable --now "$T" > /dev/null 2>&1 && echo "Zeitgeber $T abgeschaltet (schnellerer Start)."
    fi
done

# --- Sparzustand (10.11.2026): Ein-Taste 2 s halten oder Auto-Aus. Der Pi 3A+ kann nicht schlafen, darum:
#     Player, Eltern-Seite, Raspotify und WLAN-Suche beenden, WLAN aus, kleine Wache (sparzustand.py) wartet
#     auf die Ein-Taste und schaltet nach der eingestellten Zeit (Standard 6 Std) ganz aus.
#     Aufwachen: Startton sofort, parallel WLAN an und Dienste starten (peppa-aufwachen).
#     Root-Helfer als root-eigene Kopie (die Dienste laufen als root, die Datei im Repository darf der Benutzer aendern).
sudo install -d -m 0755 -o root -g root /usr/local/lib/peppa-box
sudo install -m 0755 -o root -g root "$ORDNER/sparen.sh" /usr/local/lib/peppa-box/sparen
sudo tee /etc/systemd/system/peppa-standby.service > /dev/null <<EOF
# Peppa Box (erzeugt von dienst_einrichten.sh): Sparzustand. Nicht aktiviert: wird vom Player gestartet.
[Unit]
Description=Peppa Box Sparzustand (WLAN aus, wartet auf die Ein-Taste)
After=peppa-stille.service NetworkManager.service

[Service]
Type=simple
User=$BENUTZER
WorkingDirectory=$ORDNER
# "+" = als root. Beenden und WLAN aus; beim Verlassen (auch beim Ausschalten) WLAN wieder an, denn
# NetworkManager merkt sich "WLAN aus" ueber einen Neustart
ExecStartPre=+/usr/local/lib/peppa-box/sparen ein
ExecStart=/usr/bin/python3 $ORDNER/sparzustand.py
ExecStopPost=+/usr/local/lib/peppa-box/sparen wlan-an
Environment=PYTHONUNBUFFERED=1
Restart=no
EOF
sudo tee /etc/systemd/system/peppa-aufwachen.service > /dev/null <<EOF
# Peppa Box (erzeugt von dienst_einrichten.sh): aus dem Sparzustand aufwachen. Wird von sparzustand.py gestartet.
[Unit]
Description=Peppa Box aufwachen (WLAN an, Dienste starten)

[Service]
Type=oneshot
ExecStart=/usr/local/lib/peppa-box/sparen aus
TimeoutStartSec=60
EOF
# Sicherung: ging die Box (leerer Akku, Netzteil gezogen) im Sparzustand aus, ohne dass "WLAN an" lief,
# kaeme sie sonst ohne WLAN hoch (NetworkManager merkt sich "aus"). Beim Hochfahren immer WLAN an.
if command -v nmcli > /dev/null; then
    sudo tee /etc/systemd/system/peppa-wlan-an.service > /dev/null <<EOF
# Peppa Box (erzeugt von dienst_einrichten.sh): nach dem Hochfahren WLAN sicher an (Sicherung zum Sparzustand)
[Unit]
Description=Peppa Box WLAN sicher an
After=NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=oneshot
ExecStart=-$(command -v nmcli) radio wifi on

[Install]
WantedBy=multi-user.target
EOF
fi

# --- Eltern-Seite
sudo tee /etc/systemd/system/peppa-web.service > /dev/null <<EOF
[Unit]
Description=Peppa Box Eltern-Seite
After=network-online.target
Wants=network-online.target

[Service]
User=$BENUTZER
WorkingDirectory=$ORDNER
ExecStart=/usr/bin/python3 $ORDNER/peppa_web.py
Environment=PYTHONUNBUFFERED=1
# Port 80 ohne root-Rechte erlauben (sonst nur 8080)
AmbientCapabilities=CAP_NET_BIND_SERVICE
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

# --- Helfer fuer die Kopfhoerer-Umschaltung: root-eigene Kopie (die Datei im Repository darf der
#     Benutzer aendern, die Kopie nicht; sudo erlaubt nur die Kopie mit genau diesen Argumenten)
HELFER=/usr/local/sbin/peppa-ausgang
sudo install -m 0755 -o root -g root "$ORDNER/peppa_ausgang.sh" "$HELFER"

# --- Tonausgabe und Ereignis-Programm fuer Raspotify: root-eigene Kopien ausserhalb von /home
#     (Raspotify darf /home nicht lesen). lautsprecher_einrichten.sh traegt sie in Raspotify ein.
sudo install -d -m 0755 -o root -g root /usr/local/lib/peppa-box
sudo install -m 0755 -o root -g root "$ORDNER/ausgabe.py" /usr/local/lib/peppa-box/ausgabe
sudo install -m 0755 -o root -g root "$ORDNER/ereignis.py" /usr/local/lib/peppa-box/ereignis
# WLANs eintragen/entfernen (Eltern-Seite → WLAN): Name und Passwort kommen ueber die Standardeingabe
sudo install -m 0755 -o root -g root "$ORDNER/wlan_hinzufuegen.sh" /usr/local/lib/peppa-box/wlan

# --- sudo-Freigabe: genau diese Befehle, sonst nichts
TMP="$(mktemp)"
cat > "$TMP" <<EOF
# Peppa Box: Befehle fuer Eltern-Seite (peppa-web) und Selbstreparatur des Players. Erzeugt von dienst_einrichten.sh.
$BENUTZER ALL=(root) NOPASSWD: $SYSTEMCTL poweroff, $SYSTEMCTL reboot, $SYSTEMCTL restart peppa-player, $SYSTEMCTL restart raspotify, $SYSTEMCTL restart peppa-stille, $SYSTEMCTL start --no-block peppa-standby.service, $SYSTEMCTL start --no-block peppa-aufwachen.service, $HELFER zeigen, $HELFER neustart, $HELFER lautsprecher, $HELFER kopfhoerer, /usr/local/lib/peppa-box/wlan
EOF
if sudo visudo -cf "$TMP" > /dev/null; then
    sudo install -m 0440 -o root -g root "$TMP" /etc/sudoers.d/peppa-box
else
    echo "Fehler in der sudo-Freigabe, nicht eingerichtet."; rm -f "$TMP"; exit 1
fi
rm -f "$TMP"

# --- WLAN-Suche: ohne Verbindung alle 10 s nach WLANs suchen (Handy-Hotspot unterwegs schnell finden).
#     Root-eigene Kopie ausserhalb von /home, laeuft als root (nmcli rescan).
if command -v nmcli > /dev/null; then
    sudo install -d -m 0755 -o root -g root /usr/local/lib/peppa-box
    sudo install -m 0755 -o root -g root "$ORDNER/wlan_suche.sh" /usr/local/lib/peppa-box/wlan_suche
    sudo tee /etc/systemd/system/peppa-wlan-suche.service > /dev/null <<EOF
# Peppa Box (erzeugt von dienst_einrichten.sh): WLAN-Suche, solange keine Verbindung besteht
[Unit]
Description=Peppa Box WLAN-Suche
After=NetworkManager.service
Wants=NetworkManager.service

[Service]
ExecStart=/bin/sh /usr/local/lib/peppa-box/wlan_suche
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    SUCHE_NEU=1
    # Heim-WLAN (und schon eingetragene Hotspots): nach Fehlversuchen nie aufgeben
    for f in /etc/NetworkManager/system-connections/peppa-wlan*.nmconnection; do
        sudo test -f "$f" || continue
        if ! sudo grep -q '^autoconnect-retries=' "$f"; then
            sudo sed -i '/^autoconnect-priority=/a autoconnect-retries=0' "$f"
            echo "WLAN $(basename "$f" .nmconnection): gibt nach Fehlversuchen nie auf (ab dem naechsten Start)."
        fi
    done
fi

# --- Gruppen (nur die, die es auf dem System gibt)
for G in i2c adm video audio gpio spi input; do
    if getent group "$G" > /dev/null; then sudo usermod -aG "$G" "$BENUTZER"; fi
done

# --- Raspotify erst starten, wenn das Netz steht (sonst Fehlstart "Service unavailable" und
#     ca. 20 s bis zum automatischen Neustart). Zusatzdatei, die Raspotify-Unit selbst bleibt unveraendert.
if systemctl cat raspotify.service > /dev/null 2>&1; then
    sudo mkdir -p /etc/systemd/system/raspotify.service.d
    sudo tee /etc/systemd/system/raspotify.service.d/peppa-netz.conf > /dev/null <<EOF
# Peppa Box (erzeugt von dienst_einrichten.sh): auf das Netz warten, bei Fehlern schnell neu starten
[Unit]
Wants=network-online.target
After=network-online.target

[Service]
Restart=always
RestartSec=3

[Unit]
# nie aufgeben (sonst bliebe Raspotify nach mehreren Abstuerzen aus)
StartLimitIntervalSec=0
EOF
    # network-online.target wartet nur, wenn der Warte-Dienst des Netzwerkmanagers aktiv ist
    if systemctl cat NetworkManager-wait-online.service > /dev/null 2>&1; then
        sudo systemctl enable NetworkManager-wait-online.service > /dev/null 2>&1 || true
    fi
    echo "Raspotify wartet beim Start auf das Netz (wirkt ab dem naechsten Einschalten)."
fi

# --- Protokoll ueber Neustarts hinweg behalten (vorher nur im Arbeitsspeicher: nach einem Neustart
#     war die Ursache eines Fehlers weg, Befund 09.11.2026). Hoechstens 100 MB, schont die SD-Karte
#     (journald schreibt gesammelt). Die Eltern-Seite zeigt unter "Diagnose" auch den vorigen Lauf.
sudo mkdir -p /etc/systemd/journald.conf.d
if [ ! -f /etc/systemd/journald.conf.d/peppa-box.conf ]; then
    printf '%s\n' "# Peppa Box (erzeugt von dienst_einrichten.sh): Protokoll dauerhaft" "[Journal]" \
        "Storage=persistent" "SystemMaxUse=100M" \
        | sudo tee /etc/systemd/journald.conf.d/peppa-box.conf > /dev/null
    sudo mkdir -p /var/log/journal
    sudo systemd-tmpfiles --create --prefix /var/log/journal > /dev/null 2>&1 || true
    sudo systemctl restart systemd-journald || true
    sudo journalctl --flush > /dev/null 2>&1 || true
    echo "Protokoll bleibt jetzt auch nach einem Neustart erhalten."
fi

# --- Hardware-Waechter des Pi: haengt das ganze System (Kernel, systemd) laenger als 15 s, startet der
#     Pi neu (bcm2835: hoechstens 15 s). Wirkt ab dem naechsten Einschalten.
sudo mkdir -p /etc/systemd/system.conf.d
if [ ! -f /etc/systemd/system.conf.d/peppa-watchdog.conf ]; then
    printf '%s\n' "# Peppa Box (erzeugt von dienst_einrichten.sh): Hardware-Waechter" "[Manager]" "RuntimeWatchdogSec=15" \
        | sudo tee /etc/systemd/system.conf.d/peppa-watchdog.conf > /dev/null
    echo "Hardware-Waechter eingerichtet (wirkt ab dem naechsten Einschalten)."
fi

# --- Sprachausgabe fuer Ansagen ohne eigene Aufnahme (pico2wave, deutsch). Ohne Internet oder bei
#     Fehlern geht es ohne weiter: Dann spielt die Box kurze Toene statt Sprache.
if ! command -v pico2wave > /dev/null && ! command -v espeak-ng > /dev/null; then
    echo "Installiere Sprachausgabe (libttspico-utils) ..."
    if ! sudo apt-get install -y --no-install-recommends libttspico-utils > /dev/null 2>&1; then
        sudo apt-get update > /dev/null 2>&1 || true
        sudo apt-get install -y --no-install-recommends libttspico-utils > /dev/null 2>&1 \
            || sudo apt-get install -y --no-install-recommends espeak-ng > /dev/null 2>&1 \
            || echo "Sprachausgabe nicht installiert (Ansagen ohne Aufnahme werden als Toene gespielt)."
    fi
fi

# --- Bildprogramm (Pillow) und Schrift fuer die Cover und die 40x40-Etiketten der Karten. Ohne geht
#     alles andere weiter; die Eltern-Seite zeigt dann bei den Etiketten einen Hinweis.
if ! python3 -c "import PIL" > /dev/null 2>&1 || ! fc-list 2> /dev/null | grep -qi dejavu; then
    echo "Installiere Bildprogramm fuer Etiketten (python3-pil) ..."
    sudo apt-get install -y --no-install-recommends python3-pil fonts-dejavu-core > /dev/null 2>&1 \
        || { sudo apt-get update > /dev/null 2>&1 || true
             sudo apt-get install -y --no-install-recommends python3-pil fonts-dejavu-core > /dev/null 2>&1 \
                 || echo "Bildprogramm nicht installiert (Etiketten gehen erst nach 'sudo apt install python3-pil')."; }
fi

# --- Lautsprecher (I2S, Software-Lautstaerke, Raspotify-Ausgabe) und Kopfhoerer-Mischer
sh "$ORDNER/lautsprecher_einrichten.sh" || echo "Lautsprecher-Einrichtung mit Fehler beendet (siehe oben)."

# --- Bedienelemente (Drehknopf, Pull-ups) in config.txt
sh "$ORDNER/bedienung_einrichten.sh" || echo "Bedienung-Einrichtung mit Fehler beendet (siehe oben)."

sudo systemctl daemon-reload
sudo systemctl enable peppa-player peppa-web peppa-startton
command -v nmcli > /dev/null && sudo systemctl enable peppa-wlan-an > /dev/null 2>&1
if [ "$SUCHE_NEU" = 1 ]; then
    sudo systemctl enable peppa-wlan-suche > /dev/null 2>&1
    sudo systemctl restart peppa-wlan-suche
    echo "WLAN-Suche aktiv (peppa-wlan-suche)."
fi
sudo systemctl restart peppa-player peppa-web
sleep 3
systemctl status peppa-player --no-pager | head -n 5
systemctl status peppa-web --no-pager | head -n 5
echo
echo "Eltern-Seite:  http://$(hostname).local   (oder http://$(hostname).local:8080)"
echo "Protokoll:     journalctl -u peppa-player -u peppa-web -f"
