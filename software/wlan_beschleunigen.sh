#!/bin/sh
# WLAN-Start beschleunigen: Verbindung direkt im NetworkManager speichern statt ueber Netplan.
# Hintergrund (Messung 02.11.2026): Der NetworkManager rechnet beim Start viermal "netplan generate"
# (je ca. 3,4 s auf dem Pi 3A+), bevor er das WLAN anfasst. Die WLAN-Anmeldung selbst dauert < 1 s.
#
#   sh wlan_beschleunigen.sh            umstellen (danach: sudo reboot)
#   sh wlan_beschleunigen.sh --zurueck  alten Zustand wiederherstellen (danach: sudo reboot)
#
# Was passiert:
#   1. SSID und Passwort der laufenden Netplan-WLAN-Verbindung werden auf dem Pi in eine
#      NetworkManager-Datei uebernommen (/etc/NetworkManager/system-connections/peppa-wlan.nmconnection,
#      nur fuer root lesbar). Das Passwort verlaesst den Pi nicht und wird nicht angezeigt.
#   2. Die Netplan-Dateien aus /etc/netplan wandern nach /etc/netplan.peppa-sicherung (nicht geloescht).
#   3. Rueckfall-Sicherung: Dienst peppa-wlan-rueckfall prueft nach jedem Start, ob das WLAN innerhalb
#      von 120 s verbunden ist. Wenn nicht und eine Sicherung existiert: alter Zustand zurueck,
#      NetworkManager neu starten.
# Erst nach "sudo reboot" wirksam; die laufende Verbindung (z. B. SSH) bleibt bis dahin bestehen.
set -e
NETPLAN="${PEPPA_NETPLAN:-/etc/netplan}"
SICHERUNG="${PEPPA_NETPLAN_SICHERUNG:-/etc/netplan.peppa-sicherung}"
NMDIR="${PEPPA_NM_CONNECTIONS:-/etc/NetworkManager/system-connections}"
SYSTEMD="${PEPPA_SYSTEMD:-/etc/systemd/system}"
ORDNER="$(cd "$(dirname "$0")" && pwd)"
KEYFILE="$NMDIR/peppa-wlan.nmconnection"

if [ "$1" = "--zurueck" ]; then
    if ! sudo test -d "$SICHERUNG"; then
        echo "Keine Sicherung gefunden ($SICHERUNG). Nichts zu tun."
        exit 0
    fi
    sudo sh -c "mv '$SICHERUNG'/* '$NETPLAN'/ 2> /dev/null; rmdir '$SICHERUNG'; rm -f '$KEYFILE'"
    echo "Netplan-Dateien zurueck, peppa-wlan entfernt. Jetzt: sudo reboot"
    exit 0
fi

if sudo test -f "$KEYFILE"; then
    echo "Schon umgestellt ($KEYFILE vorhanden). Rueckweg: sh $0 --zurueck"
    exit 0
fi

# --- 1. aktive WLAN-Verbindung ermitteln (nur Netplan-Verbindungen)
VERB="$(nmcli -t -f NAME,TYPE,DEVICE connection show --active | awk -F: '$2=="802-11-wireless" && $1 ~ /^netplan-/ {print $1; exit}')"
if [ -z "$VERB" ]; then
    echo "Keine aktive Netplan-WLAN-Verbindung gefunden. Abbruch, nichts geaendert."
    nmcli -f NAME,TYPE,DEVICE connection show --active || true
    exit 1
fi
SSID="$(nmcli -e no -t -g 802-11-wireless.ssid connection show "$VERB")"
KEYMGMT="$(nmcli -e no -t -g 802-11-wireless-security.key-mgmt connection show "$VERB")"
PSK="$(sudo nmcli -e no -s -t -g 802-11-wireless-security.psk connection show "$VERB")"
if [ -z "$SSID" ] || [ "$KEYMGMT" != "wpa-psk" ] || [ -z "$PSK" ]; then
    echo "WLAN '$VERB': SSID/Passwort nicht lesbar oder kein WPA-Passwort (key-mgmt '$KEYMGMT'). Abbruch, nichts geaendert."
    exit 1
fi
echo "WLAN-Verbindung: $VERB (SSID $SSID) wird uebernommen."

# --- Keyfile schreiben (Werte fuer das Keyfile-Format maskieren: Backslash, fuehrendes Leerzeichen)
maske() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/^ /\\s/'; }
UUID="$(cat /proc/sys/kernel/random/uuid)"
TMP="$(mktemp)"
chmod 600 "$TMP"
cat > "$TMP" <<EOF
# Peppa Box (erzeugt von wlan_beschleunigen.sh): WLAN direkt im NetworkManager, ohne Netplan
[connection]
id=peppa-wlan
uuid=$UUID
type=wifi
autoconnect=true
autoconnect-priority=10
autoconnect-retries=0

[wifi]
mode=infrastructure
ssid=$(maske "$SSID")
powersave=2

[wifi-security]
key-mgmt=wpa-psk
psk=$(maske "$PSK")

[ipv4]
method=auto

[ipv6]
method=auto
addr-gen-mode=default

[proxy]
EOF
PSK=""
sudo mkdir -p "$NMDIR"
sudo install -m 0600 -o root -g root "$TMP" "$KEYFILE"
rm -f "$TMP"

# --- 2. Netplan-Dateien sichern
sudo mkdir -p "$SICHERUNG"
sudo sh -c "for f in '$NETPLAN'/*.yaml; do [ -e \"\$f\" ] && mv \"\$f\" '$SICHERUNG'/; done; true"
echo "Netplan-Dateien gesichert nach $SICHERUNG"

# --- 3. Rueckfall-Sicherung
sudo tee "$SYSTEMD/peppa-wlan-rueckfall.service" > /dev/null <<EOF
# Peppa Box (erzeugt von wlan_beschleunigen.sh): alten WLAN-Zustand wiederherstellen, wenn das
# WLAN nach dem Start nicht innerhalb von 120 s verbunden ist
[Unit]
Description=Peppa Box WLAN-Rueckfall-Sicherung
After=NetworkManager.service

[Service]
Type=oneshot
ExecStart=/bin/sh $ORDNER/wlan_rueckfall.sh

[Install]
WantedBy=multi-user.target
EOF
if [ -z "$PEPPA_TROCKEN" ]; then
    sudo systemctl daemon-reload
    sudo systemctl enable peppa-wlan-rueckfall > /dev/null 2>&1
fi
echo "Rueckfall-Sicherung aktiv (stellt nach 120 s ohne WLAN den alten Zustand her)."
echo "Fertig. Jetzt: sudo reboot   (Rueckweg jederzeit: sh $0 --zurueck)"
