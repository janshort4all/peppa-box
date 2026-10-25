#!/bin/sh
# Richtet den Player als Dienst ein: startet beim Einschalten, startet nach Fehlern neu.
# Aufruf (als normaler Benutzer, nicht als root):  sh ~/peppa-box/software/dienst_einrichten.sh
set -e
BENUTZER="$(id -un)"
ORDNER="$(cd "$(dirname "$0")" && pwd)"
if [ "$BENUTZER" = "root" ]; then
    echo "Bitte ohne sudo aufrufen, das Skript fragt selbst nach dem Passwort."; exit 1
fi
sudo tee /etc/systemd/system/peppa-player.service > /dev/null <<EOF
[Unit]
Description=Peppa Box Player (Karten, Spotify, Einstellungsseite)
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
sudo systemctl daemon-reload
sudo systemctl enable --now peppa-player
sleep 3
systemctl status peppa-player --no-pager | head -n 12
echo
echo "Protokoll ansehen:  journalctl -u peppa-player -f"
