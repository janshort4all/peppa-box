#!/bin/sh
# WLAN-Suche fuer die Peppa Box (laeuft als root ueber peppa-wlan-suche.service, Steckbrief 09.11.2026).
# Ohne Verbindung sucht der NetworkManager immer seltener nach WLANs (bis etwa alle 2 Minuten).
# Wird der Handy-Hotspot erst spaeter eingeschaltet, dauert es dann lange, bis die Box ihn findet.
# Dieses Skript stoesst deshalb alle 10 s eine Suche an, aber nur, solange das WLAN wirklich getrennt
# ist (nicht waehrend einer Anmeldung, nicht bei bestehender Verbindung). Die Verbindung selbst baut
# der NetworkManager auf (gespeicherte WLANs, hoechste Prioritaet zuerst).
INTERVALL="${PEPPA_SUCHE_INTERVALL:-10}"
RUHE="${PEPPA_SUCHE_RUHE:-30}"
VORHER=""

while :; do
    ZUSTAND="$(nmcli -t -f TYPE,STATE device 2> /dev/null | sed -n 's/^wifi://p' | head -n 1)"
    case "$ZUSTAND" in
    connected*)
        if [ "$VORHER" != verbunden ]; then
            echo "WLAN verbunden: $(nmcli -t -g GENERAL.CONNECTION device show wlan0 2> /dev/null)"
        fi
        VORHER=verbunden
        PAUSE="$RUHE" ;;
    disconnected)
        if [ "$VORHER" != getrennt ]; then echo "WLAN getrennt, suche alle ${INTERVALL} s."; fi
        VORHER=getrennt
        nmcli device wifi rescan > /dev/null 2>&1 || true   # "laeuft schon" u. ae. ist egal
        PAUSE="$INTERVALL" ;;
    *)  PAUSE="$INTERVALL" ;;   # Anmeldung laeuft, WLAN aus o. ae.: nichts tun
    esac
    [ -n "$PEPPA_SUCHE_EINMAL" ] && exit 0
    sleep "$PAUSE"
done
