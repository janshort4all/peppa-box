"""G-Code-Prüfung Korpus (ElegooSlicer, Klipper): Fuzzy innen/außen, glattes Anschlussfeld, Fasen, Naht, Lüfter, Schichtzeit.
Aufruf: python3 gcode_pruefung.py datei.gcode  → Zusammenfassung; Schichtdaten in gcode_schichten.json.
Lage des Korpus auf dem Bett wird aus den glatten Schichten der oberen Fase bestimmt (Mitte der Außenkontur = Modell x/y 70)."""
import re, sys, math, json
import numpy as np

GC = sys.argv[1]
OX = OY = 0.0                                          # wird nach dem Einlesen bestimmt
W, R = 140.0, 16.0
SCV = 5.0                                              # square_corner_velocity (Annahme Klipper-Standard)


def d_out(x, y):
    h = W / 2 - R
    qx, qy = abs(x - W / 2) - h, abs(y - W / 2) - h
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - R


layers = []          # je Schicht: dict
cur = None
x = y = 0.0
f = 3000.0
accel = 10000.0
typ = None
path = []            # aktuelle Außenwand-Bahn: Liste (x, y)
moves = []           # (länge, v_soll, accel, ux, uy) für die Zeitrechnung
fan = None

def flush_path():
    global path
    if cur is not None and len(path) >= 2:
        cur["paths"].append((typ_path, path))
    path = []

typ_path = None
rx = re.compile(r'([XYZEF])(-?[\d.]+)')
with open(GC, errors="replace") as fh:
    for line in fh:
        if line.startswith(";LAYER_CHANGE"):
            flush_path()
            cur = dict(z=None, paths=[], moves=[], fan=[], types={}, brim=[], ext_len={})
            layers.append(cur)
            continue
        if line.startswith(";Z:") and cur is not None:
            cur["z"] = float(line[3:])
            continue
        if line.startswith(";TYPE:"):
            flush_path()
            typ = line[6:].strip()
            continue
        if line.startswith("SET_VELOCITY_LIMIT"):
            m = re.search(r"ACCEL=([\d.]+)", line)
            if m:
                accel = float(m.group(1))
            continue
        if line.startswith("M204"):
            m = re.search(r"S([\d.]+)", line)
            if m:
                accel = float(m.group(1))
            continue
        if line.startswith("M106") and cur is not None:
            m = re.search(r"\bS([\d.]+)", line)
            if m and " P" not in line:
                cur["fan"].append(int(float(m.group(1))))
            continue
        if line.startswith("G1") or line.startswith("G0") or line.startswith("G2") or line.startswith("G3"):
            d = dict(rx.findall(line.split(";")[0]))
            if "F" in d:
                f = float(d["F"])
            nx = float(d.get("X", x)); ny = float(d.get("Y", y))
            e = float(d.get("E", 0.0))
            L = math.hypot(nx - x, ny - y)
            if cur is not None and L > 1e-6:
                cur["moves"].append((L, f / 60.0, accel, (nx - x) / L, (ny - y) / L))
                if e > 0:
                    cur["ext_len"][typ] = cur["ext_len"].get(typ, 0.0) + L
                if e > 0 and typ in ("Outer wall", "Overhang wall"):
                    if not path or (abs(path[-1][0] - x) > 1e-6 or abs(path[-1][1] - y) > 1e-6):
                        flush_path()
                        path = [(x, y)]
                        typ_path = typ
                    path.append((nx, ny))
                elif e > 0 and typ == "Brim":
                    cur["brim"].append(((x + nx) / 2, (y + ny) / 2))
                elif path:
                    flush_path()
            x, y = nx, ny


def layer_time(moves):
    """Trapez-Planer mit Kurvengeschwindigkeit nach Klipper (Junction Deviation aus SCV)."""
    n = len(moves)
    if n == 0:
        return 0.0
    L = np.array([m[0] for m in moves]); V = np.array([m[1] for m in moves]); A = np.array([m[2] for m in moves])
    U = np.array([(m[3], m[4]) for m in moves])
    vj = np.zeros(n + 1)                                   # Geschwindigkeit am Übergang i (vor Bewegung i)
    cosang = np.clip(-(U[1:] * U[:-1]).sum(1), -0.999999, 0.999999)
    sin_half = np.sqrt(0.5 * (1.0 - cosang))
    a = np.minimum(A[1:], A[:-1])
    jd = SCV ** 2 * (math.sqrt(2) - 1) / a
    vjs = np.sqrt(np.maximum(a * jd * sin_half / np.maximum(1 - sin_half, 1e-9), 0))
    vj[1:n] = np.minimum(np.minimum(vjs, V[1:]), V[:-1])
    # vorwärts
    for i in range(n):
        vj[i + 1] = min(vj[i + 1], math.sqrt(vj[i] ** 2 + 2 * A[i] * L[i]))
    for i in range(n - 1, -1, -1):
        vj[i] = min(vj[i], math.sqrt(vj[i + 1] ** 2 + 2 * A[i] * L[i]))
    t = 0.0
    for i in range(n):
        v0, v1, vm, a_, l = vj[i], vj[i + 1], V[i], A[i], L[i]
        vp = min(vm, math.sqrt((2 * a_ * l + v0 ** 2 + v1 ** 2) / 2))
        da = (vp ** 2 - v0 ** 2) / (2 * a_); dd = (vp ** 2 - v1 ** 2) / (2 * a_)
        dc = max(l - da - dd, 0.0)
        t += (vp - v0) / a_ + (vp - v1) / a_ + dc / vp
    return t


def zigzag(pts):
    """Fuzzy-Maß je Punkt: Abweichung von der Sehne der Nachbarn, aber nur bei wechselnder Krümmungsrichtung
    (Fuzzy springt abwechselnd nach außen und innen; Kreise und Rundungen krümmen gleichsinnig)."""
    p = np.asarray(pts)
    if len(p) < 4:
        return np.zeros(len(p))
    a, b, c = p[:-2], p[1:-1], p[2:]
    ac = c - a
    n = np.hypot(ac[:, 0], ac[:, 1]) + 1e-12
    cr = (b[:, 0] - a[:, 0]) * ac[:, 1] - (b[:, 1] - a[:, 1]) * ac[:, 0]
    dist = np.abs(cr) / n
    seg = np.minimum(np.hypot(*(b - a).T), np.hypot(*(c - b).T))
    sg = np.sign(cr)
    alt = np.zeros(len(sg), bool)
    alt[1:] |= sg[1:] != sg[:-1]
    alt[:-1] |= sg[:-1] != sg[1:]
    out = np.zeros(len(p))
    out[1:-1] = np.where((seg < 0.6) & alt, dist, 0.0)
    return out


_top = [l for l in layers if l["z"] and 135.1 < l["z"] < 135.9 and l["paths"]]
_P = np.vstack([np.asarray(p) for l in _top[:1] for _, p in l["paths"]])
OX, OY = (_P[:, 0].min() + _P[:, 0].max()) / 2 - 70.0, (_P[:, 1].min() + _P[:, 1].max()) / 2 - 70.0
res = []
for i, Lr in enumerate(layers):
    zp = Lr["z"]
    r = dict(layer=i + 1, z=zp, fuzzy_innen=0, fuzzy_aussen=0, glatt_aussen=0, fuzzy_glattfeld=0, pkt_innen=0,
             fan=sorted(set(Lr["fan"])), fan_n=len(Lr["fan"]), seam=None, brim=len(Lr["brim"]), types=Lr["ext_len"])
    seams = []
    for t_, pts in Lr["paths"]:
        p = np.asarray(pts) - [OX, OY]
        zz = zigzag(p)
        fz = zz > 0.03
        dd = np.array([d_out(px, py) for px, py in p])
        innen = (dd < -1.5) & (p[:, 1] > 13.7)
        aussen = dd >= -1.5
        mz = zp + 4.0
        # Anschlussfeld hinten (x 17–123, z 46,5–69,5, R 5), 0,6 mm nach innen versetzt, damit der Rand nicht mitzählt
        qx = np.maximum(np.abs(p[:, 0] - 70.0) - (53.0 - 0.6 - 4.4), 0); qz = max(abs(mz - 58.0) - (11.5 - 0.6 - 4.4), 0)
        glattfeld = aussen & (p[:, 1] > 137.0) & (np.hypot(qx, qz) < 4.4)
        r["fuzzy_innen"] += int((fz & innen).sum()); r["pkt_innen"] += int(innen.sum())
        r["fuzzy_aussen"] += int((fz & aussen).sum()); r["glatt_aussen"] += int((~fz & aussen).sum())
        r["fuzzy_glattfeld"] += int((fz & glattfeld).sum())
        if aussen.mean() > 0.8 and len(p) > 50:
            seams.append((len(p), p[0].tolist()))
    if seams:
        r["seam"] = max(seams)[1]
    r["zeit"] = layer_time(Lr["moves"])
    res.append(r)
import os
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(GC)), "gcode_schichten.json"), "w"))
z = np.array([r["z"] for r in res]); t = np.array([r["zeit"] for r in res])
fi = np.array([r["fuzzy_innen"] for r in res]); fa = np.array([r["fuzzy_aussen"] for r in res])
print(f"Schichten {len(res)}, Lage Bett→Modell {OX:.2f}/{OY:.2f}, Druckzeit nachgerechnet {t.sum()/3600:.1f} h")
print(f"Fuzzy-Punkte außen {fa.sum()}, innen {fi.sum()} (max {fi.max()} je Schicht; Einzelpunkte an kleinen Rundungen sind normal, Fuzzy-Wand innen wären >1000)")
print(f"Fuzzy im glatten Anschlussfeld: {sum(r['fuzzy_glattfeld'] for r in res)}; Fase unten (z≤0,8): {fa[z<0.81].sum()}; Fase oben (z>135): {fa[z>135.05].sum()}")
print(f"Lüfterbefehle je Schicht: Median {np.median([r['fan_n'] for r in res]):.0f}; Werte: {sorted(set(v for r in res for v in r['fan']))}")
print(f"Schichtdauer Median {np.median(t):.0f} s; Schichten > 2× Median: " + ", ".join(f"{a:.1f} mm ({b:.0f} s)" for a, b in zip(z, t) if b > 2*np.median(t)))

# Sprünge in der Schichtdauer (zeichnen sich bei PETG außen als Linie ab): Abweichung vom gleitenden Median ±10 Schichten
med = np.array([np.median(t[max(0, i - 10):i + 11]) for i in range(len(t))])
spr = [(a, b, c) for a, b, c in zip(z, t, med) if a > 3 and abs(b - c) > 0.25 * c]
print(f"Schichtdauer-Sprünge > 25 % (ab 3 mm): {len(spr)}" + (": " + ", ".join(f"{a:.1f} mm ({b:.0f} s statt {c:.0f})" for a, b, c in spr[:20]) if spr else " – gut"))
