#!/usr/bin/env python3
"""Gegenprobe mit fremder Bibliothek: pimylifeup/MFRC522-python (unveraendert).

Zweck: pruefen, ob der RC522 Karten liest, ohne eigenen Code.
Vorher einmal:  git clone https://github.com/pimylifeup/MFRC522-python ~/MFRC522-python
Start:          python3 ~/peppa-box/software/rc522_ref_test.py      Beenden: Strg+C

RPi.GPIO wird nur durch eine leere Attrappe ersetzt: Die Bibliothek wuerde damit den RST-Pin
auf HIGH setzen. RST liegt bei uns ohnehin fest an 3,3 V, alles andere laeuft ueber SPI.
"""
import os
import sys
import time
import types

gpio = types.ModuleType("RPi.GPIO")
gpio.BOARD, gpio.BCM, gpio.OUT = 10, 11, 0
gpio.getmode = lambda: 10
gpio.setmode = gpio.setup = gpio.output = gpio.cleanup = gpio.setwarnings = lambda *a, **k: None
rpi = types.ModuleType("RPi")
rpi.GPIO = gpio
sys.modules["RPi"] = rpi
sys.modules["RPi.GPIO"] = gpio

sys.path.insert(0, os.path.expanduser("~/MFRC522-python"))
try:
    from mfrc522 import MFRC522
except ImportError:
    print("Bibliothek fehlt. Bitte zuerst:  git clone https://github.com/pimylifeup/MFRC522-python ~/MFRC522-python")
    sys.exit(1)

r = MFRC522()
print(f"Referenz-Bibliothek geladen, RC522 Version 0x{r.Read_MFRC522(0x37):02X}. Karte auflegen, Beenden mit Strg+C.")
gesehen = 0
t_info = time.time()
try:
    while True:
        status, bits = r.MFRC522_Request(r.PICC_REQIDL)
        if status == r.MI_OK:
            gesehen += 1
            status, uid = r.MFRC522_Anticoll()
            if status == r.MI_OK:
                print("Karte:", ":".join(f"{b:02X}" for b in uid[:4]))
            else:
                print("Karte geantwortet, Nummer aber nicht lesbar")
        if time.time() - t_info > 3:
            print(f"  ... laeuft (bisher {gesehen} gueltige Antworten)")
            t_info = time.time()
        time.sleep(0.2)
except KeyboardInterrupt:
    print()
finally:
    r.spi.close()
