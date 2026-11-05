"""G-Code-Prüfung Deckel (kopfüber, zweifarbig). Aufruf: python3 gcode_deckel_pruefung.py deckel.gcode

Prüft: Farbe je Schicht und je Fläche (Symbole/Ringe orange, Rest beige in den Haut-Schichten), Brücken über den Feldern,
Wände in den Haut-Schichten (Modifier 02m: 1 Wand), Fahrwege über Vertiefungen (nur alter Aufbau), Naht, erste Schicht.
Lage auf dem Bett: Mitte der Außenwand von Schicht 2 = Deckelmitte (Deckel um y gedreht, wie M.deckel_kopfueber).
"""
import os, re, sys, math, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as M
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely import make_valid

FARBE = {}          # Werkzeug-Nummer → Name, aus den Kopfzeilen (filament_colour) nicht sicher → nur Nummern ausgeben


def lesen(f):
    layers, cur, tool, typ = [], None, None, None
    x = y = 0.0
    for ln in open(f, encoding="utf-8", errors="ignore"):
        if ln.startswith(";LAYER_CHANGE"):
            cur = dict(n=len(layers) + 1, z=None, segs=[], travel=[], tools=[tool])
            layers.append(cur); continue
        if ln.startswith(";Z:") and cur is not None:
            cur["z"] = float(ln[3:]); continue
        if ln.startswith(";TYPE:"):
            typ = ln[6:].strip(); continue
        m = re.match(r"^T(\d+)", ln)
        if m:
            tool = int(m.group(1))
            if cur is not None: cur["tools"].append(tool)
            continue
        if ln[:3] in ("G1 ", "G0 ", "G2 ", "G3 "):
            d = dict((k, float(v)) for k, v in re.findall(r"([XYZEF])(-?[\d.]+)", ln.split(";")[0]))
            nx, ny = d.get("X", x), d.get("Y", y)
            if cur is not None and (nx, ny) != (x, y):
                if d.get("E", 0) > 0:
                    cur["segs"].append((typ, tool, x, y, nx, ny))
                else:
                    cur["travel"].append((x, y, nx, ny))
            x, y = nx, ny
    return layers


def main(f):
    L = lesen(f)
    print(f"Schichten {len(L)}")
    ow = np.array([s[2:] for s in L[1]["segs"] if s[0] == "Outer wall"])
    cx = (ow[:, [0, 2]].min() + ow[:, [0, 2]].max()) / 2; cy = (ow[:, [1, 3]].min() + ow[:, [1, 3]].max()) / 2
    lb = M.LID_CS.bounds()
    OX, OY = cx + (lb[0] + lb[2]) / 2, cy - (lb[1] + lb[3]) / 2
    fx = lambda x, y: (OX - x, y + OY)

    def shp(cs):
        g = None
        for q in cs.to_polygons():
            q = np.asarray(q)
            if len(q) < 3: continue
            q = make_valid(Polygon([fx(*a) for a in q])); g = q if g is None else g.symmetric_difference(q)
        return g
    sym = shp(M.pad_symbols())
    felder = unary_union([Polygon([fx(x + d / 2 * math.cos(t), y + d / 2 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 90)])
                          for x, y, d in M.PADS.values()])
    haut = int(round(M.SKIN / 0.2))
    print(f"Lage: Bett X = {OX:.2f} − x, Bett Y = y + {OY:.2f}; Haut = Schicht 1–{haut}")

    # 1) Farben je Schicht und je Fläche
    for l in L[:haut + 1]:
        tl = [t for t in dict.fromkeys(l["tools"]) if t is not None]
        im, aus = collections.Counter(), collections.Counter()
        for typ, t, a, b, c, d in l["segs"]:
            if typ == "Prime tower": continue
            mid = LineString([(a, b), (c, d)]).interpolate(0.5, normalized=True)
            (im if sym.buffer(-0.25).contains(mid) else aus if not sym.buffer(0.25).contains(mid) else collections.Counter())[t] += math.hypot(c - a, d - b)
        typen = collections.Counter()
        for typ, t, a, b, c, d in l["segs"]:
            typen[typ] += math.hypot(c - a, d - b)
        print(f"  Schicht {l['n']} (z {l['z']}): Werkzeuge {tl}; in Symbolen/Ringen {dict((k, round(v)) for k, v in im.items())} mm, "
              f"außerhalb {dict((k, round(v)) for k, v in aus.items())} mm; Innenwand {round(typen.get('Inner wall', 0))} mm, Brücke {round(typen.get('Bridge', 0))} mm")
    # 2) Brücken über den Feldern (alter Aufbau: Böden der Vertiefungen)
    for l in L[:haut + 3]:
        br = [LineString([(a, b), (c, d)]) for typ, t, a, b, c, d in l["segs"] if typ == "Bridge"]
        if br:
            fl = unary_union([b_.buffer(0.2, cap_style=2) for b_ in br]).intersection(felder).area
            ang = [math.degrees(math.atan2(b_.coords[1][1] - b_.coords[0][1], b_.coords[1][0] - b_.coords[0][0])) % 180 for b_ in br if b_.length > 1]
            print(f"  Schicht {l['n']}: Brücke über den Feldern {fl:.0f} mm² (Vertiefungen {sym.area:.0f}, Felder {felder.area:.0f} mm²); "
                  f"Richtung (Bett) 10/50/90 %: {np.percentile(ang, [10, 50, 90]).round(0).tolist() if ang else '-'}°")
    # 3) Fahrwege über Vertiefungen in den Haut-Schichten (nur wenn die Haut Löcher hat)
    inner = sym.buffer(-0.15)
    for l in L[1:haut]:
        hit = [LineString([(a, b), (c, d)]) for a, b, c, d in l["travel"]]
        hit = [t for t in hit if t.intersects(inner)]
        if hit:
            print(f"  Schicht {l['n']}: {len(hit)} Fahrwege über Symbol-/Ringflächen (bei eingelegten Symbolen harmlos, bei Vertiefungen Fadengefahr)")
    # 4) erste Schicht und Naht
    first = collections.Counter(s[0] for s in L[0]["segs"])
    print("Schicht 1:", "UMRANDUNG vorhanden!" if any(k in ("Brim", "Skirt") for k in first) else "keine Umrandung")
    seam = []
    for l in L:
        segs = [s for s in l["segs"] if s[0] == "Outer wall"]
        if not segs: continue
        loops, cur_ = [], [segs[0]]
        for s0, s1 in zip(segs, segs[1:]):
            if math.hypot(s1[2] - s0[4], s1[3] - s0[5]) > 0.5: loops.append(cur_); cur_ = []
            cur_.append(s1)
        loops.append(cur_)
        big = max(loops, key=lambda lp: sum(math.hypot(q[4] - q[2], q[5] - q[3]) for q in lp))
        seam.append((round(OX - big[0][2], 1), round(big[0][3] - OY, 1)))
    print(f"Naht Außenkontur (Deckelkoordinaten, y 0 = vorne): x {min(a for a, b in seam)}–{max(a for a, b in seam)}, "
          f"y {min(b for a, b in seam)}–{max(b for a, b in seam)}")
    wechsel = sum(1 for l in L for a, b in zip(l["tools"], l["tools"][1:]) if a is not None and b is not None and a != b)
    print(f"Farbwechsel gesamt: {wechsel}")


if __name__ == "__main__":
    main(sys.argv[1])
