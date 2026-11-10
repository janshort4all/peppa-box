#!/bin/sh
# Peppa Box: Root-Helfer fuer den Sparzustand. Installiert von dienst_einrichten.sh als
# /usr/local/lib/peppa-box/sparen (root-eigene Kopie), aufgerufen von den Diensten peppa-standby und
# peppa-aufwachen (laufen als root), nicht ueber sudo.
#   ein      Betrieb beenden (Player, Eltern-Seite, Raspotify, WLAN-Suche), WLAN aus
#   aus      WLAN an, Player und Eltern-Seite sofort starten, Raspotify sobald das WLAN steht
#   wlan-an  nur das WLAN an. Muss vor jedem Ausschalten aus dem Sparzustand laufen: NetworkManager
#            merkt sich "WLAN aus" ueber einen Neustart, die Box startete sonst ohne WLAN.
# Jeder Schritt wird einzeln versucht, ein Fehler haelt die anderen nicht auf.
SYSTEMCTL="${PEPPA_SYSTEMCTL:-systemctl}"
NMCLI="${PEPPA_NMCLI:-nmcli}"
NMONLINE="${PEPPA_NMONLINE:-nm-online}"
BETRIEB="peppa-player.service peppa-web.service raspotify.service peppa-wlan-suche.service"

case "$1" in
    ein)
        for d in $BETRIEB; do
            "$SYSTEMCTL" stop "$d" 2> /dev/null || echo "sparen: $d liess sich nicht beenden"
        done
        "$NMCLI" radio wifi off || echo "sparen: WLAN liess sich nicht ausschalten"
        exit 0 ;;
    aus)
        "$NMCLI" radio wifi on || echo "sparen: WLAN liess sich nicht einschalten"
        # Player und Eltern-Seite brauchen kein Netz: sofort (Tasten, Klick, Karten)
        "$SYSTEMCTL" start --no-block peppa-player.service peppa-web.service peppa-wlan-suche.service
        # Raspotify startet sonst vor dem WLAN, scheitert ("Service unavailable") und braucht Neustarts
        "$NMONLINE" -q -t 25 || echo "sparen: kein WLAN nach 25 s, Raspotify startet trotzdem"
        "$SYSTEMCTL" start --no-block raspotify.service
        exit 0 ;;
    wlan-an)
        "$NMCLI" radio wifi on || { echo "sparen: WLAN liess sich nicht einschalten"; exit 1; }
        exit 0 ;;
    *)
        echo "Aufruf: sparen ein|aus|wlan-an"
        exit 2 ;;
esac
