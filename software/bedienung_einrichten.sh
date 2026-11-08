#!/bin/sh
# Richtet die Bedienelemente in config.txt ein. Wird von dienst_einrichten.sh aufgerufen, kann aber
# auch allein laufen. Beliebig oft wiederholbar; aendert nur, was fehlt oder anders ist.
#   dtparam=i2c_arm=on    Touch-Chip MPR121, Akku-Chip INA219
#   dtparam=spi=on        Kartenleser RC522
#   dtparam=audio=on      Pi-Klinke (Kopfhoerer)
#   dtoverlay=rotary-encoder,pin_a=17,pin_b=27,relative_axis=1,steps-per-period=2
#                         Drehknopf STEC11B03 (15 Impulse / 30 Rasten = halber Takt je Raste) an P17/P27;
#                         der Kernel liest ihn per Interrupt, das Overlay schaltet die Pull-ups ein
#   gpio=5=ip,pu          MPR121 INT an P05 (Pull-up zusaetzlich zu dem auf der Adafruit-Platine)
#   gpio=26=ip,pu         Klinke, Oeffner L an P26 (Steckererkennung)
# Die Ein-Taste an SCL braucht nichts: Der Pi wacht aus dem ausgeschalteten Zustand auf, wenn GPIO 3
# nach Masse gezogen wird; im Betrieb liest der Player den Pegel von SCL.
# Wirkt erst nach einem Neustart (sudo reboot); das Skript sagt, wenn einer noetig ist.
set -e
CFG="${PEPPA_CONFIG_TXT:-/boot/firmware/config.txt}"
NEUSTART=0

if [ ! -f "$CFG" ]; then
    echo "config.txt ($CFG) nicht gefunden. Bedienung NICHT eingerichtet."
    exit 1
fi
LETZTER_ABSCHNITT="$(grep '^\[' "$CFG" | tail -n 1 || true)"
if [ -n "$LETZTER_ABSCHNITT" ] && [ "$LETZTER_ABSCHNITT" != "[all]" ]; then
    echo "config.txt endet nicht mit [all], sondern mit $LETZTER_ABSCHNITT. Bedienung NICHT eingerichtet."
    exit 1
fi

zeile_sicherstellen() {   # $1 = Zeile, $2 = Anfang zum Erkennen; vorhandene andere Fassung wird ersetzt
    if grep -q "^$1\$" "$CFG"; then
        return
    fi
    if grep -q "^$2" "$CFG"; then
        sudo sed -i "s|^$2.*|$1|" "$CFG"
        echo "config.txt: auf '$1' geaendert."
    else
        echo "$1" | sudo tee -a "$CFG" > /dev/null
        echo "config.txt: '$1' ergaenzt."
    fi
    NEUSTART=1
}

zeile_sicherstellen "dtparam=i2c_arm=on" "dtparam=i2c_arm="
zeile_sicherstellen "dtparam=spi=on" "dtparam=spi="
zeile_sicherstellen "dtparam=audio=on" "dtparam=audio="
zeile_sicherstellen "dtoverlay=rotary-encoder,pin_a=17,pin_b=27,relative_axis=1,steps-per-period=2" "dtoverlay=rotary-encoder"
zeile_sicherstellen "gpio=5=ip,pu" "gpio=5="
zeile_sicherstellen "gpio=26=ip,pu" "gpio=26="

# /dev/i2c-1 gibt es nur mit dem Kernel-Modul i2c-dev. raspi-config laedt es beim Einschalten von I2C,
# ein frisch aufgesetztes System ohne raspi-config nicht (Befund 08.11.2026: Touch-Chip "/dev/i2c-1 fehlt").
MODULE="${PEPPA_MODULES_LOAD:-/etc/modules-load.d}/peppa-i2c.conf"
if [ ! -f "$MODULE" ] && ! grep -qs '^i2c-dev' /etc/modules; then
    echo "i2c-dev" | sudo tee "$MODULE" > /dev/null
    sudo modprobe i2c-dev 2> /dev/null || true
    echo "Kernel-Modul i2c-dev wird jetzt beim Start geladen."
fi

if [ "$NEUSTART" = 1 ]; then
    echo "config.txt wurde geaendert: Bitte einmal neu starten (sudo reboot)."
else
    echo "Bedienung: config.txt ist schon richtig eingestellt."
fi
