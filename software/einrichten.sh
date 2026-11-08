#!/bin/sh
# Komplett-Einrichtung der Peppa Box auf einer frisch bespielten SD-Karte (Raspberry Pi OS Lite 64-bit).
#
# Vorbereitung am PC (Karte noch im Kartenleser, Laufwerk "bootfs"):
#   Ordner "peppa" mit dieser Datei und peppa-box.bundle auf das Laufwerk kopieren.
#   Optional: github-token.txt (Lese-Token fuer das Repository, damit Updates ueber die Eltern-Seite gehen).
#   Optional: spotify-client-id.txt (Client-ID der Spotify-Entwickler-App).
# Am Pi (per SSH, als normaler Benutzer):
#   sh /boot/firmware/peppa/einrichten.sh
#
# Das Skript ist wiederholbar: Was schon erledigt ist, wird uebersprungen. Am Ende Neustart.
# Zugangsdaten (Token, Spotify) landen nur auf dem Pi, nie im Repository.
set -e
QUELLE="$(cd "$(dirname "$0")" && pwd)"
BENUTZER="$(id -un)"
REPO="$HOME/peppa-box"
GITHUB="https://github.com/janshort4all/peppa-box"
KONF="$HOME/.config/peppa-box"
RASPOTIFY=/etc/raspotify/conf

schritt() { printf '\n=== %s ===\n' "$1"; }

if [ "$BENUTZER" = "root" ]; then
    echo "Bitte ohne sudo aufrufen: sh $0"; exit 1
fi
echo "Peppa Box einrichten. Das dauert etwa 10-20 Minuten. sudo fragt einmal nach deinem Passwort."
sudo -v

schritt "1/7 Pakete"
sudo apt-get update
sudo apt-get install -y --no-install-recommends git curl alsa-utils python3-spidev

schritt "2/7 Programm (Repository)"
if [ -d "$REPO/.git" ]; then
    echo "Schon vorhanden: $REPO"
elif [ -f "$QUELLE/peppa-box.bundle" ]; then
    git clone -q "$QUELLE/peppa-box.bundle" "$REPO"
    git -C "$REPO" remote set-url origin "$GITHUB"
    echo "Aus dem Paket entpackt: $(git -C "$REPO" log -1 --format='%h %s')"
else
    git clone -q "$GITHUB" "$REPO"
fi
if [ -f "$QUELLE/github-token.txt" ]; then
    TOKEN="$(tr -d ' \r\n' < "$QUELLE/github-token.txt")"
    git -C "$REPO" config credential.helper store
    umask 077
    printf 'https://x-access-token:%s@github.com\n' "$TOKEN" > "$HOME/.git-credentials"
    umask 022
    sudo rm -f "$QUELLE/github-token.txt"          # nicht auf der lesbaren Boot-Partition liegen lassen
    echo "GitHub-Zugang gespeichert (nur auf dem Pi)."
fi
if git -C "$REPO" fetch -q origin 2> /dev/null; then
    git -C "$REPO" branch -q --set-upstream-to=origin/main main 2> /dev/null || true
    if git -C "$REPO" merge -q --ff-only origin/main 2> /dev/null; then
        echo "Auf dem neuesten Stand: $(git -C "$REPO" log -1 --format='%h %s')"
    fi
else
    echo "Hinweis: GitHub nicht erreichbar oder kein Zugang. Updates ueber die Eltern-Seite gehen erst mit Token."
fi

schritt "3/7 Raspotify (Spotify-Lautsprecher)"
if ! command -v librespot > /dev/null && ! systemctl cat raspotify.service > /dev/null 2>&1; then
    curl -sSL https://dtcooper.github.io/raspotify/install.sh | sh
fi
setze() {   # $1 Schluessel, $2 Wert: vorhandene (auch auskommentierte) Zeile ersetzen, sonst anhaengen
    if sudo grep -q "^#\?$1=" "$RASPOTIFY"; then
        sudo sed -i "s|^#\?$1=.*|$1=$2|" "$RASPOTIFY"
    else
        echo "$1=$2" | sudo tee -a "$RASPOTIFY" > /dev/null
    fi
}
if sudo test -f "$RASPOTIFY"; then
    setze LIBRESPOT_NAME '"Peppa Box"'
    setze LIBRESPOT_VOLUME_CTRL fixed
    setze LIBRESPOT_INITIAL_VOLUME 100
    sudo sed -i 's|^LIBRESPOT_DISABLE_CREDENTIAL_CACHE=|#LIBRESPOT_DISABLE_CREDENTIAL_CACHE=|' "$RASPOTIFY"
    sudo systemctl restart raspotify 2> /dev/null || true   # neue Einstellungen (Zugangsdaten merken) wirksam
    echo "Raspotify eingestellt (Name, feste Lautstaerke, Zugangsdaten merken)."
else
    echo "FEHLER: $RASPOTIFY fehlt, Raspotify-Installation hat nicht geklappt."; exit 1
fi

schritt "4/7 WLAN schneller starten"
sh "$REPO/software/wlan_beschleunigen.sh" || echo "WLAN-Umstellung uebersprungen (siehe oben)."

schritt "5/7 Dienste, Lautsprecher, Bedienelemente"
sh "$REPO/software/dienst_einrichten.sh"

schritt "6/7 Spotify-Anmeldung"
mkdir -p "$KONF"
if [ -f "$QUELLE/spotify-client-id.txt" ] && [ ! -f "$KONF/config.json" ]; then
    CID="$(tr -d ' \r\n' < "$QUELLE/spotify-client-id.txt")"
    printf '{"client_id": "%s"}\n' "$CID" > "$KONF/config.json"
fi
if [ -f "$KONF/spotify_token.json" ]; then
    echo "Schon angemeldet."
else
    echo "Client-ID findest du unter https://developer.spotify.com/dashboard (deine App -> Settings)."
    python3 "$REPO/software/spotify_login.py" || echo "Anmeldung nicht abgeschlossen. Spaeter: python3 $REPO/software/spotify_login.py"
fi

schritt "7/7 Box in der Spotify-App bekannt machen"
if sudo test -f /var/lib/raspotify/credentials.json; then
    echo "Raspotify kennt dein Konto schon."
else
    sudo systemctl restart raspotify 2> /dev/null || true   # sicher mit der aktuellen Einstellung
    echo "Jetzt am Handy: Spotify-App -> etwas abspielen -> Geraete -> 'Peppa Box' waehlen."
    echo "Ich warte bis zu 5 Minuten ..."
    i=0
    while [ "$i" -lt 60 ] && ! sudo test -f /var/lib/raspotify/credentials.json; do
        sleep 5; i=$((i + 1))
    done
    if sudo test -f /var/lib/raspotify/credentials.json; then
        echo "Gefunden, Raspotify merkt sich das Konto."
    else
        echo "Nicht erkannt. Das kannst du nach dem Neustart nachholen (Peppa Box in der Spotify-App waehlen)."
    fi
fi

# Zweiter Durchlauf nach dem Neustart: Die Verstaerker-Karte (hifiberry-dac) erscheint erst nach dem
# Neustart, erst dann kann lautsprecher_einrichten.sh Mischer, Regler und Raspotify-Ausgang anlegen
# (Befund 08.11.2026). Einmal-Dienst: laeuft nach dem Neustart, entfernt sich und startet noch einmal neu.
if ! grep -qi hifiberry /proc/asound/cards 2> /dev/null; then
    if sudo -n true 2> /dev/null; then
        sudo tee /etc/systemd/system/peppa-einrichten-2.service > /dev/null <<EOF
[Unit]
Description=Peppa Box Einrichtung, zweiter Durchlauf (einmalig)
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=oneshot
User=$BENUTZER
ExecStart=/bin/sh -c 'sh $REPO/software/dienst_einrichten.sh > $HOME/einrichtung-2.log 2>&1; sudo systemctl disable peppa-einrichten-2; sudo rm -f /etc/systemd/system/peppa-einrichten-2.service; sudo reboot'

[Install]
WantedBy=multi-user.target
EOF
        sudo systemctl daemon-reload
        sudo systemctl enable peppa-einrichten-2 > /dev/null 2>&1
        echo "Nach dem Neustart folgt automatisch der zweite Durchlauf (Lautsprecher), danach noch ein Neustart."
        echo "Protokoll: ~/einrichtung-2.log. Insgesamt ca. 3 Minuten, bis die Ansage kommt."
    else
        echo "WICHTIG: Nach dem Neustart noch einmal ausfuehren: sh $REPO/software/dienst_einrichten.sh && sudo reboot"
    fi
fi

printf '\nFertig. Die Box startet jetzt neu. Danach: Eltern-Seite http://peppabox.local\n'
sleep 3
sudo reboot
