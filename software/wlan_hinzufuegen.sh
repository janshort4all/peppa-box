#!/bin/sh
# Weitere WLANs fuer die Peppa Box eintragen, vor allem die Handy-Hotspots (Steckbrief 09.11.2026).
#
#   sh wlan_hinzufuegen.sh                  Name und Passwort abfragen, Prioritaet 5
#   sh wlan_hinzufuegen.sh --prioritaet 7   dasselbe mit anderer Prioritaet (1-9)
#   sh wlan_hinzufuegen.sh --liste          gespeicherte WLANs der Box anzeigen
#   sh wlan_hinzufuegen.sh --entfernen NAME ein eingetragenes WLAN wieder loeschen
#   sh wlan_hinzufuegen.sh --roh            Liste fuer Programme: je Zeile Prioritaet, Art (heim/weitere), Name, mit Tab getrennt
#
# Die Eltern-Seite (peppa_web.py) ruft die root-eigene Kopie /usr/local/lib/peppa-box/wlan per sudo auf
# (Name und Passwort kommen ueber die Standardeingabe, nie als Aufrufargument: sonst stuenden sie in
# der Prozessliste). Name und Passwort werden dort wie hier geprueft.
#
# Welches WLAN die Box nimmt: unter den sichtbaren gespeicherten WLANs das mit der hoechsten
# Prioritaet. Heim-WLAN (peppa-wlan aus wlan_beschleunigen.sh) = 10, Hotspots = 5. Zu Hause gewinnt
# also immer das Heim-WLAN, unterwegs der Hotspot. Ist die Box verbunden, wechselt sie nicht von selbst.
#
# Die WLANs werden direkt als NetworkManager-Datei geschrieben (nicht mit "nmcli connection add",
# das legt wieder Netplan-Dateien an und macht den Start langsam). Dateien nur fuer root lesbar,
# das Passwort wird nicht angezeigt und verlaesst den Pi nicht. Eine laufende Verbindung (SSH)
# bleibt bestehen. Ausserdem bekommen alle WLANs der Box "autoconnect-retries=0": Der NetworkManager
# gibt nach Fehlversuchen nie auf (sonst sperrt er das WLAN nach 4 Versuchen fuer 5 Minuten).
set -e
NMDIR="${PEPPA_NM_CONNECTIONS:-/etc/NetworkManager/system-connections}"
HEIM="$NMDIR/peppa-wlan.nmconnection"
PRIO=5

[ "$(id -u)" = 0 ] && PEPPA_OHNE_SUDO=1     # als root (Kopie in /usr/local/lib/peppa-box) braucht es kein sudo
sudo_lauf() { if [ -n "$PEPPA_OHNE_SUDO" ]; then "$@"; else sudo "$@"; fi; }   # Tests ohne sudo
maske() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/^ /\\s/'; }
kurz() { printf '%s' "$1" | tr -c 'A-Za-z0-9_-' '_' | cut -c 1-40; }   # Dateiname aus dem WLAN-Namen
datei_zu() { printf '%s/peppa-wlan-%s.nmconnection' "$NMDIR" "$(kurz "$1")"; }
wert() { sudo_lauf sed -n "s/^$1=//p" "$2" | head -n 1; }

# Alle WLAN-Dateien der Box: nie aufgeben (fehlende Zeile hinter autoconnect-priority einfuegen)
nie_aufgeben() {
    for f in "$NMDIR"/peppa-wlan*.nmconnection; do
        sudo_lauf test -f "$f" || continue
        if ! sudo_lauf grep -q '^autoconnect-retries=' "$f"; then
            sudo_lauf sed -i '/^autoconnect-priority=/a autoconnect-retries=0' "$f"
            echo "Nie aufgeben eingestellt: $(basename "$f")"
        fi
    done
}

neu_laden() {
    [ -n "$PEPPA_TROCKEN" ] && return 0
    sudo nmcli connection reload || echo "Hinweis: nmcli connection reload fehlgeschlagen, wirkt nach sudo reboot."
}

case "$1" in
--liste)
    echo "Gespeicherte WLANs der Box (hoechste Prioritaet gewinnt):"
    for f in "$NMDIR"/peppa-wlan*.nmconnection; do
        sudo_lauf test -f "$f" || continue
        printf '  %-32s Prioritaet %s\n' "$(wert ssid "$f")" "$(wert autoconnect-priority "$f")"
    done
    exit 0 ;;
--roh)
    for f in "$NMDIR"/peppa-wlan*.nmconnection; do
        sudo_lauf test -f "$f" || continue
        if [ "$f" = "$HEIM" ]; then ART=heim; else ART=weitere; fi
        printf '%s\t%s\t%s\n' "$(wert autoconnect-priority "$f")" "$ART" "$(wert ssid "$f")"
    done
    exit 0 ;;
--entfernen)
    [ -n "$2" ] || { echo "Bitte den WLAN-Namen angeben: sh $0 --entfernen NAME"; exit 1; }
    DATEI="$(datei_zu "$2")"
    if ! sudo_lauf test -f "$DATEI"; then
        echo "WLAN '$2' ist nicht eingetragen (Liste: sh $0 --liste)."; exit 1
    fi
    sudo_lauf rm -f "$DATEI"
    neu_laden
    echo "WLAN '$2' entfernt."
    exit 0 ;;
--prioritaet)
    case "$2" in [1-9]) PRIO="$2" ;; *) echo "Prioritaet bitte 1 bis 9 (Heim-WLAN hat 10)."; exit 1 ;; esac ;;
"") ;;
*)  echo "Unbekannte Angabe '$1'. Moeglich: --liste, --roh, --entfernen NAME, --prioritaet 1-9"; exit 1 ;;
esac

# --- Name und Passwort abfragen (Passwort ohne Anzeige)
printf 'Name des WLANs bzw. Hotspots (genau wie im Handy): '
IFS= read -r SSID || true
printf 'Passwort (wird nicht angezeigt): '
if [ -t 0 ]; then stty -echo; fi
IFS= read -r PSK || true
if [ -t 0 ]; then stty echo; fi
echo

LAENGE="$(printf '%s' "$SSID" | wc -c)"
if [ -z "$SSID" ] || [ "$LAENGE" -gt 32 ]; then
    echo "Der Name muss 1 bis 32 Zeichen lang sein. Nichts geaendert."; exit 1
fi
case "$SSID" in
*[!A-Za-z0-9\ _.-]*) echo "Hinweis: Der Name enthaelt Sonderzeichen. Tippfehler (z. B. ' statt ’) verhindern die Verbindung." ;;
esac
P_LAENGE="$(printf '%s' "$PSK" | wc -c)"
if [ "$P_LAENGE" -lt 8 ] || [ "$P_LAENGE" -gt 63 ]; then
    PSK=""
    echo "Das Passwort muss 8 bis 63 Zeichen lang sein (WPA2). Nichts geaendert."; exit 1
fi
if sudo_lauf test -f "$HEIM" && [ "$(wert ssid "$HEIM")" = "$(maske "$SSID")" ]; then
    PSK=""
    echo "'$SSID' ist das Heim-WLAN der Box (peppa-wlan), das bleibt wie es ist. Nichts geaendert."; exit 1
fi

# --- Datei schreiben (gleicher Name: Datei ersetzen, Kennung behalten)
DATEI="$(datei_zu "$SSID")"
ID="peppa-wlan-$(kurz "$SSID")"
UUID=""
if sudo_lauf test -f "$DATEI"; then UUID="$(wert uuid "$DATEI")"; ALT=1; else ALT=0; fi
[ -n "$UUID" ] || UUID="$(cat /proc/sys/kernel/random/uuid)"
TMP="$(mktemp)"
chmod 600 "$TMP"
cat > "$TMP" <<EOF
# Peppa Box (erzeugt von wlan_hinzufuegen.sh): weiteres WLAN, z. B. Handy-Hotspot
[connection]
id=$ID
uuid=$UUID
type=wifi
autoconnect=true
autoconnect-priority=$PRIO
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
sudo_lauf mkdir -p "$NMDIR"
if [ -n "$PEPPA_OHNE_SUDO" ]; then cp "$TMP" "$DATEI"; chmod 600 "$DATEI"
else sudo install -m 0600 -o root -g root "$TMP" "$DATEI"; fi
rm -f "$TMP"
nie_aufgeben
neu_laden
if [ "$ALT" = 1 ]; then echo "WLAN '$SSID' aktualisiert (Prioritaet $PRIO)."
else echo "WLAN '$SSID' eingetragen (Prioritaet $PRIO)."; fi

# --- Nur zur Info: ist das WLAN gerade zu sehen? (keine Verbindung aufbauen, SSH bleibt)
if [ -z "$PEPPA_TROCKEN" ] && command -v nmcli > /dev/null; then
    if nmcli -t -f SSID device wifi list --rescan yes 2> /dev/null | grep -Fxq "$SSID"; then
        echo "Die Box sieht '$SSID' gerade."
    else
        echo "Die Box sieht '$SSID' gerade nicht (Hotspot aus oder 5 GHz?). Eingetragen ist es trotzdem."
    fi
fi
