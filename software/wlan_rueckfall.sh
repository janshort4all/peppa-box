#!/bin/sh
# Rueckfall-Sicherung fuer wlan_beschleunigen.sh (laeuft als root ueber peppa-wlan-rueckfall.service).
# Ist das WLAN 120 s nach dem Start nicht verbunden und gibt es eine Netplan-Sicherung, wird der alte
# Zustand wiederhergestellt und der NetworkManager neu gestartet. Nach dem ersten erfolgreichen Start
# schaltet sich die Sicherung selbst ab (Steckbrief 02.11.2026: sonst Rueckfall im Urlaub-WLAN).
NETPLAN="${PEPPA_NETPLAN:-/etc/netplan}"
SICHERUNG="${PEPPA_NETPLAN_SICHERUNG:-/etc/netplan.peppa-sicherung}"
KEYFILE="${PEPPA_NM_CONNECTIONS:-/etc/NetworkManager/system-connections}/peppa-wlan.nmconnection"
FRIST="${PEPPA_RUECKFALL_FRIST:-120}"

[ -d "$SICHERUNG" ] || exit 0            # nichts umgestellt -> nichts zu pruefen

i=0
while [ "$i" -lt "$FRIST" ]; do
    if nmcli -t -f DEVICE,TYPE,STATE device 2> /dev/null | grep -q ':wifi:connected$'; then
        echo "WLAN verbunden nach ca. ${i} s, alles gut."
        # Die schnelle Einstellung hat einmal funktioniert: Sicherung abschalten. Sonst nimmt sie
        # unterwegs (kein bekanntes WLAN) die Einstellung zurueck. Die Netplan-Sicherung bleibt fuer
        # den Rueckweg von Hand (wlan_beschleunigen.sh --zurueck).
        if [ -f "$KEYFILE" ] && systemctl disable peppa-wlan-rueckfall.service > /dev/null 2>&1; then
            echo "Rueckfall-Sicherung abgeschaltet (erster Start mit peppa-wlan erfolgreich)."
        fi
        exit 0
    fi
    sleep 5
    i=$((i + 5))
done

echo "WLAN nach ${FRIST} s nicht verbunden: stelle Netplan-Zustand wieder her."
mv "$SICHERUNG"/* "$NETPLAN"/ 2> /dev/null
rmdir "$SICHERUNG" 2> /dev/null
rm -f "$KEYFILE"
systemctl restart NetworkManager
exit 0
