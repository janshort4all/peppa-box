"""Link auf eine NFC-Karte vom Typ 2 (NTAG213/215/216, Ultralight) schreiben und zurücklesen.

Reine Logik über zwei Griffe der Karte (`lese16(seite)`, `schreibe4(seite, daten)`), damit sie ohne
Hardware gegen eine simulierte Karte getestet werden kann. Der Leser (rc522.py) liefert die Griffe.

Sicherheitsregeln (eine Karte lässt sich schlimmstenfalls nicht mehr beschreiben, nie unlesbar machen):
  * nur Seiten 4 bis zum Ende des Nutzerbereichs aus dem Capability Container (Seite 3) werden
    geschrieben; Seiten 0–3 (Nummer, Sperrbits, Capability Container, einmal beschreibbar) und die
    Konfigurationsseiten am Ende bleiben unberührt,
  * ist Seite 3 nicht als NDEF-Karte eingerichtet (E1 ...) oder schreibgeschützt, wird nichts geschrieben,
  * erfolgreich heißt: zurückgelesener Link ist gleich dem gewünschten, nicht "die Karte hat ACK gesagt".

Die Rückgabe ist immer dict(ok, grund, meldung, ...); Gründe: ok, nicht_ndef, schreibgeschuetzt,
zu_gross, lesefehler, schreibfehler, pruefung.
"""
import ndef

ERSTE_SEITE = 4
MIN_BYTES, MAX_BYTES = 48, 888                 # Ultralight EV1 (48) bis NTAG216 (888)


def _ergebnis(ok, grund, meldung, **mehr):
    return dict(ok=ok, grund=grund, meldung=meldung, **mehr)


def kapazitaet(karte):
    """(Bytes im Nutzerbereich, Grund) – Bytes ist None, wenn die Karte nicht beschrieben werden darf."""
    kopf = karte.lese16(0)
    if not kopf or len(kopf) < 16:
        return None, _ergebnis(False, "lesefehler", "Die Karte ließ sich nicht lesen. Bitte ruhig aufliegen lassen und noch einmal versuchen.")
    cc = kopf[12:16]
    if cc[0] != 0xE1:
        return None, _ergebnis(False, "nicht_ndef", "Die Karte ist nicht für Links eingerichtet. Sie wird in der Box gemerkt, ein Handy kann sie aber nicht lesen.")
    if cc[3] & 0x0F:
        return None, _ergebnis(False, "schreibgeschuetzt", "Die Karte ist schreibgeschützt. Sie wird in der Box gemerkt.")
    gross = cc[2] * 8
    if not MIN_BYTES <= gross <= MAX_BYTES:
        return None, _ergebnis(False, "nicht_ndef", "Die Größe der Karte ist ungewöhnlich, sie wird nicht beschrieben.")
    return gross, None


def link_lesen(karte, bytes_=MAX_BYTES):
    """Link aus dem Nutzerbereich lesen (None = keiner, Ausnahme bei Lesefehler)."""
    daten = []
    for seite in range(ERSTE_SEITE, ERSTE_SEITE + (bytes_ + 3) // 4, 4):
        block = karte.lese16(seite)
        if not block:
            raise OSError("Lesefehler")
        daten += list(block)
        nachricht = ndef.ndef_aus_tlv(daten)
        if nachricht is not ndef.FEHLT:
            return ndef.uri_aus_ndef(nachricht) if nachricht else None
    return None


def ntag_beschreiben(karte, link):
    gross, fehler = kapazitaet(karte)
    if fehler:
        return fehler
    try:
        tlv = ndef.tlv_fuer_link(link)
    except ValueError:
        return _ergebnis(False, "zu_gross", "Der Link ist zu lang für eine Karte.")
    if len(tlv) > gross:
        return _ergebnis(False, "zu_gross", "Der Link passt nicht auf diese Karte.")
    daten = tlv + bytes(-len(tlv) % 4)                         # auf ganze Seiten auffüllen
    for i in range(0, len(daten), 4):
        if not karte.schreibe4(ERSTE_SEITE + i // 4, daten[i:i + 4]):
            return _ergebnis(False, "schreibfehler", "Beim Schreiben hat die Karte nicht geantwortet. Karte ruhig aufliegen lassen und noch einmal versuchen.")
    try:
        gelesen = link_lesen(karte, gross)
    except OSError:
        return _ergebnis(False, "lesefehler", "Die Karte ließ sich danach nicht zurücklesen. Bitte noch einmal versuchen.")
    if gelesen != link:
        return _ergebnis(False, "pruefung", "Die Prüfung nach dem Schreiben stimmt nicht. Bitte noch einmal versuchen.")
    return _ergebnis(True, "ok", "Der Link steht jetzt auf der Karte.", bytes=len(tlv), kapazitaet=gross)
