#!/bin/sh
# Richtet die Dienste der Peppa Box ein. Beide starten beim Einschalten und nach Fehlern neu.
#   peppa-player  Karten lesen, Spotify steuern
#   peppa-web     Eltern-Seite (Zustand, Neustart, Ausschalten, Update), Port 80 und 8080
# Dazu: sudo-Freigabe nur fuer die Befehle, die die Eltern-Seite braucht (/etc/sudoers.d/peppa-box),
# und die Gruppen fuer Akku (i2c), Protokoll (adm), Stromversorgung (video) und Lautstaerke (audio).
# Ausserdem den Lautsprecher (lautsprecher_einrichten.sh) und: Raspotify startet erst mit Netz.
# Und: WLAN-Stromsparen aus (sonst nach einer Weile nicht mehr erreichbar).
# Aufruf (als normaler Benutzer, nicht als root):  sh ~/peppa-box/software/dienst_einrichten.sh
# Kann beliebig oft wiederholt werden.
set -e
BENUTZER="$(id -un)"
ORDNER="$(cd "$(dirname "$0")" && pwd)"
SYSTEMCTL="$(command -v systemctl)"
if [ "$BENUTZER" = "root" ]; then
    echo "Bitte ohne sudo aufrufen, das Skript fragt selbst nach dem Passwort."; exit 1
fi

# --- Player
sudo tee /etc/systemd/system/peppa-player.service > /dev/null <<EOF
[Unit]
Description=Peppa Box Player (Karten, Spotify)
After=network-online.target raspotify.service
Wants=network-online.target

[Service]
User=$BENUTZER
WorkingDirectory=$ORDNER
ExecStart=/usr/bin/python3 $ORDNER/peppa_player.py
Environment=PYTHONUNBUFFERED=1
Restart=always
RestartSec=5

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

# --- cloud-init abschalten: braucht nur der allererste Start (Raspberry Pi Imager: WLAN, Benutzer),
#     kostet danach bei jedem Start ca. 4-5 s. Rueckgaengig: sudo rm /etc/cloud/cloud-init.disabled
if [ -d /etc/cloud ] && [ ! -f /etc/cloud/cloud-init.disabled ]; then
    sudo touch /etc/cloud/cloud-init.disabled
    echo "cloud-init abgeschaltet (schnellerer Start ab dem naechsten Einschalten)."
fi

# --- Alter Startton-Dienst (02.11.2026 kurz eingebaut, ersetzt durch die Ansage im Player): entfernen
if [ -f /etc/systemd/system/peppa-startton.service ]; then
    sudo systemctl disable peppa-startton > /dev/null 2>&1 || true
    sudo rm -f /etc/systemd/system/peppa-startton.service
    echo "Alter Startton-Dienst entfernt."
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

# --- sudo-Freigabe: genau diese Befehle, sonst nichts
TMP="$(mktemp)"
cat > "$TMP" <<EOF
# Peppa Box: Befehle fuer die Eltern-Seite (peppa-web). Erzeugt von dienst_einrichten.sh.
$BENUTZER ALL=(root) NOPASSWD: $SYSTEMCTL poweroff, $SYSTEMCTL reboot, $SYSTEMCTL restart peppa-player, $SYSTEMCTL restart raspotify
EOF
if sudo visudo -cf "$TMP" > /dev/null; then
    sudo install -m 0440 -o root -g root "$TMP" /etc/sudoers.d/peppa-box
else
    echo "Fehler in der sudo-Freigabe, nicht eingerichtet."; rm -f "$TMP"; exit 1
fi
rm -f "$TMP"

# --- Gruppen (nur die, die es auf dem System gibt)
for G in i2c adm video audio; do
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
RestartSec=3
EOF
    # network-online.target wartet nur, wenn der Warte-Dienst des Netzwerkmanagers aktiv ist
    if systemctl cat NetworkManager-wait-online.service > /dev/null 2>&1; then
        sudo systemctl enable NetworkManager-wait-online.service > /dev/null 2>&1 || true
    fi
    echo "Raspotify wartet beim Start auf das Netz (wirkt ab dem naechsten Einschalten)."
fi

# --- Lautsprecher (I2S, Software-Lautstaerke, Raspotify-Ausgabe)
sh "$ORDNER/lautsprecher_einrichten.sh" || echo "Lautsprecher-Einrichtung mit Fehler beendet (siehe oben)."

sudo systemctl daemon-reload
sudo systemctl enable peppa-player peppa-web
sudo systemctl restart peppa-player peppa-web
sleep 3
systemctl status peppa-player --no-pager | head -n 5
systemctl status peppa-web --no-pager | head -n 5
echo
echo "Eltern-Seite:  http://$(hostname).local   (oder http://$(hostname).local:8080)"
echo "Protokoll:     journalctl -u peppa-player -u peppa-web -f"
