#!/bin/sh
# WLAN-Suche fuer die Peppa Box (laeuft als root ueber peppa-wlan-suche.service, Steckbrief 09.11.2026).
# Ohne Verbindung sucht der NetworkManager immer seltener nach WLANs (bis etwa alle 2 Minuten).
# Wird der Handy-Hotspot erst spaeter eingeschaltet, dauert es dann lange, bis die Box ihn findet.
# Dieses Skript stoesst deshalb alle 10 s eine Suche an, aber nur, solange das WLAN wirklich getrennt
# ist (nicht waehrend einer Anmeldung, nicht bei bestehender Verbindung). Die Verbindung selbst baut
# der NetworkManager auf (gespeicherte WLANs, hoechste Prioritaet zuerst).
#
# Anstoss (Befund 17.11.2026, Box kam erst nach einem Router-Neustart wieder ins WLAN): Ist das WLAN
# ANSTOSS_NACH s lang nicht verbunden und ist ein gespeichertes WLAN in Reichweite (oder gar kein WLAN
# zu sehen, dann haengt vermutlich der Funk), wird das WLAN neu angestossen: abwechselnd Funk aus/an
# und NetworkManager neu starten, hoechstens alle ANSTOSS_ABSTAND s. Bei ausgeschaltetem Funk
# (Sparzustand, "unavailable") passiert nichts. Wird das Skript waehrend "Funk aus" beendet, schaltet
# es den Funk wieder ein (der NetworkManager merkt sich "aus" sonst ueber einen Neustart).
INTERVALL="${PEPPA_SUCHE_INTERVALL:-10}"
RUHE="${PEPPA_SUCHE_RUHE:-30}"
ANSTOSS_NACH="${PEPPA_ANSTOSS_NACH:-120}"
ANSTOSS_ABSTAND="${PEPPA_ANSTOSS_ABSTAND:-300}"
RUNDEN="${PEPPA_SUCHE_RUNDEN:-0}"          # 0 = endlos (Tests: Anzahl Durchlaeufe)
[ -n "$PEPPA_SUCHE_EINMAL" ] && RUNDEN=1
VORHER=""
T=0                 # Sekunden seit dem Start (aus den Pausen gezaehlt)
OHNE=""             # seit wann (T) ohne Verbindung
LETZTER=""          # T des letzten Anstosses
ART=funk            # naechster Anstoss: funk | nm
FUNK_AUS=""

trap '[ -n "$FUNK_AUS" ] && nmcli radio wifi on; exit 0' TERM INT

bekannt_in_reichweite() {
    SICHT="$(nmcli -t -f SSID device wifi list --rescan no 2> /dev/null | grep -v '^$')"
    [ -z "$SICHT" ] && return 0                     # gar nichts zu sehen: Funk haengt vermutlich
    nmcli -t -f NAME,TYPE connection show 2> /dev/null | sed -n 's/:802-11-wireless$//p' |
    while IFS= read -r NAME; do
        NAME="$(printf '%s' "$NAME" | sed 's/\\:/:/g')"
        S="$(nmcli -t -g 802-11-wireless.ssid connection show "$NAME" 2> /dev/null)"
        [ -n "$S" ] && printf '%s\n' "$SICHT" | grep -qxF "$S" && echo ja
    done | grep -q ja
}

anstossen() {
    if [ "$ART" = funk ]; then
        echo "WLAN seit $((T - OHNE)) s nicht verbunden: Funk aus und wieder an."
        FUNK_AUS=1
        nmcli radio wifi off > /dev/null 2>&1
        sleep 3 & wait $!
        nmcli radio wifi on > /dev/null 2>&1
        FUNK_AUS=""
        ART=nm
    else
        echo "WLAN seit $((T - OHNE)) s nicht verbunden: NetworkManager neu gestartet."
        systemctl restart NetworkManager > /dev/null 2>&1
        ART=funk
    fi
    LETZTER=$T
}

N=0
while :; do
    ZUSTAND="$(nmcli -t -f TYPE,STATE device 2> /dev/null | sed -n 's/^wifi://p' | head -n 1)"
    case "$ZUSTAND" in
    connected*)
        if [ "$VORHER" != verbunden ]; then
            echo "WLAN verbunden: $(nmcli -t -g GENERAL.CONNECTION device show wlan0 2> /dev/null)"
        fi
        VORHER=verbunden
        OHNE=""
        ART=funk
        PAUSE="$RUHE" ;;
    disconnected)
        if [ "$VORHER" != getrennt ]; then echo "WLAN getrennt, suche alle ${INTERVALL} s."; fi
        VORHER=getrennt
        [ -z "$OHNE" ] && OHNE=$T
        nmcli device wifi rescan > /dev/null 2>&1 || true   # "laeuft schon" u. ae. ist egal
        PAUSE="$INTERVALL" ;;
    connecting*)    # Anmeldung laeuft: keine Suche, aber eine haengende Anmeldung zaehlt als "ohne"
        [ -z "$OHNE" ] && OHNE=$T
        PAUSE="$INTERVALL" ;;
    *)  OHNE=""     # WLAN aus (Sparzustand) o. ae.: nichts tun
        PAUSE="$INTERVALL" ;;
    esac
    if [ -n "$OHNE" ] && [ $((T - OHNE)) -ge "$ANSTOSS_NACH" ] &&
       { [ -z "$LETZTER" ] || [ $((T - LETZTER)) -ge "$ANSTOSS_ABSTAND" ]; } &&
       [ "$(nmcli radio wifi 2> /dev/null)" = enabled ] && bekannt_in_reichweite; then
        anstossen
    fi
    N=$((N + 1))
    [ "$RUNDEN" -gt 0 ] && [ "$N" -ge "$RUNDEN" ] && exit 0
    sleep "$PAUSE" & wait $!                # "wait" laesst sich sofort beenden (Sparzustand wartet nicht)
    T=$((T + PAUSE))
done
