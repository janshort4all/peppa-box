"""NDEF (Typ-2-Karten, MIFARE-Classic-Sektoren): Link aus der Karte lesen und für das Schreiben bauen.

Reine Rechenfunktionen ohne Hardware (läuft auch auf dem Entwicklungsrechner und in den Tests).
rc522.py (Leser) und kartenschreiber.py (Karte beschreiben) nutzen sie gemeinsam.
"""
FEHLT = object()                            # Marker: TLV noch nicht vollstaendig gelesen

URI_PREFIX = ["", "http://www.", "https://www.", "http://", "https://", "tel:", "mailto:",
              "ftp://anonymous:anonymous@", "ftp://ftp.", "ftps://", "sftp://", "smb://", "nfs://",
              "ftp://", "dav://", "news:", "telnet://", "imap:", "rtsp://", "urn:", "pop:", "sip:",
              "sips:", "tftp:", "btspp://", "btl2cap://", "btgoep://", "tcpobex://", "irdaobex://",
              "file://", "urn:epc:id:", "urn:epc:tag:", "urn:epc:pat:", "urn:epc:raw:", "urn:epc:",
              "urn:nfc:"]


def ndef_aus_tlv(daten):
    """Sucht im TLV-Bereich die NDEF-Nachricht. Gibt Bytes, None (keine) oder FEHLT (mehr lesen) zurueck."""
    i = 0
    while i < len(daten):
        t = daten[i]
        if t == 0x00:                          # Fuellbyte
            i += 1
            continue
        if t == 0xFE:                          # Ende
            return None
        if i + 1 >= len(daten):
            return FEHLT
        laenge, kopf = daten[i + 1], 2
        if laenge == 0xFF:
            if i + 3 >= len(daten):
                return FEHLT
            laenge, kopf = (daten[i + 2] << 8) | daten[i + 3], 4
        if i + kopf + laenge > len(daten):
            return FEHLT
        if t == 0x03:
            return bytes(daten[i + kopf:i + kopf + laenge])
        i += kopf + laenge                     # andere TLVs (Lock, Memory) ueberspringen
    return FEHLT


def uri_aus_ndef(nachricht):
    """Erster URI-Datensatz (oder Text, der wie ein Link aussieht) aus einer NDEF-Nachricht."""
    i = 0
    while i < len(nachricht):
        kopf = nachricht[i]
        tnf, kurz, mit_id = kopf & 0x07, kopf & 0x10, kopf & 0x08
        typ_l = nachricht[i + 1]
        j = i + 2
        if kurz:
            nutz_l = nachricht[j]; j += 1
        else:
            nutz_l = int.from_bytes(nachricht[j:j + 4], "big"); j += 4
        id_l = 0
        if mit_id:
            id_l = nachricht[j]; j += 1
        typ = nachricht[j:j + typ_l]; j += typ_l + id_l
        nutz = nachricht[j:j + nutz_l]
        if tnf == 1 and typ == b"U" and nutz:
            vorne = URI_PREFIX[nutz[0]] if nutz[0] < len(URI_PREFIX) else ""
            return vorne + nutz[1:].decode("utf-8", "replace")
        if tnf == 1 and typ == b"T" and nutz:
            text = nutz[1 + (nutz[0] & 0x3F):].decode("utf-8", "replace").strip()
            if "spotify" in text:
                return text
        if kopf & 0x40:                        # letzter Datensatz
            break
        i = j + nutz_l
    return None




def uri_datensatz(link):
    """NDEF-Datensatz "URI" (kurze Form) für einen Link. https://open.spotify.com/... wird mit dem
    Kürzel 0x04 ("https://") gespeichert; jeder andere Anfang geht ungekürzt (Kürzel 0)."""
    praefix = 0
    for nr in (2, 4, 1, 3):                  # längere Anfänge zuerst: https://www., https://, http://www., http://
        if link.startswith(URI_PREFIX[nr]):
            praefix = nr
            break
    nutz = bytes([praefix]) + link[len(URI_PREFIX[praefix]):].encode("utf-8")
    if len(nutz) > 255:
        raise ValueError("Link zu lang")
    return bytes([0xD1, 0x01, len(nutz), 0x55]) + nutz       # MB+ME+SR, TNF 1, Typ "U"


def tlv_fuer_nachricht(nachricht):
    """NDEF-Nachricht in den TLV-Bereich einer Typ-2-Karte packen (Tag 0x03 ... Ende 0xFE)."""
    n = len(nachricht)
    laenge = bytes([n]) if n < 0xFF else bytes([0xFF, n >> 8, n & 0xFF])
    return bytes([0x03]) + laenge + nachricht + bytes([0xFE])


def tlv_fuer_link(link):
    return tlv_fuer_nachricht(uri_datensatz(link))
