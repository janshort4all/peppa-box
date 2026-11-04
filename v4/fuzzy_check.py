"""Fuzzy-Skin-Prüfung Schicht für Schicht – bildet die Logik von ElegooSlicer nach (v1.5.2.2 und v1.5.3.5, Quellcode
src/libslic3r/Feature/FuzzySkin/FuzzySkin.cpp, Layer.cpp, PrintApply.cpp; gelesen am 04.11.2026).

So entscheidet der Slicer:
  1. Jede Schicht wird geschnitten. Jede geschlossene Randlinie ist entweder KONTUR (Außenrand einer Insel) oder LOCH.
     Das hängt nur von der Form der Schicht ab, nicht davon, ob die Fläche außen oder innen am Gehäuse liegt.
  2. Regionen mit unterschiedlichem Fuzzy werden für die Wände NICHT getrennt (fuzzy_skin fehlt in
     Layer::is_perimeter_compatible). Die Außenwand-Schleife wird an den Grenzen der Modifier-Bereiche nur zerteilt;
     jedes Stück bekommt Fuzzy, wenn seine Region es für diesen Schleifentyp (Kontur/Loch) vorsieht.
  3. „Kontur“ = Fuzzy auf der äußersten Schleife jeder KONTUR.

Folge: Geht ein Loch ganz durch die Wand (Klinke, Drehgeber, USB-C, Schlitze, Riemen, Deckelschrauben, Lautsprecher),
ist der Wandring in diesen Schichten aufgeschnitten. Die Schicht ist dann ein „C“ – eine einzige Insel, deren Kontur
außen herum, durch das Loch und innen an der Wand entlang zurück läuft. Die ganze Innenseite gehört zur Kontur und
wird mit „verfuzzt“.

Berechnet für jede 0,2-mm-Schicht, wie viele mm Außenwand-Schleife Fuzzy bekommen – innen und außen –
für (A) den gedruckten Aufbau (alles „Kontur“, Modifier 01m ohne Fuzzy) und (B) den neuen Aufbau
(Objekt „Deaktiviert“, Modifier 01f „Kontur“ nur in einer 1-mm-Außenhaut).
"""
import os as _os
import sys
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely import contains_xy
from shapely.ops import unary_union

import model as M
import modifier as MD
from manifold3d import JoinType

ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
OUTDIR = _os.path.join(ROOT, "v4", "out")

LAYER = 0.2
FIRST = 0.2
W_EXT = 0.42            # Linienbreite Außenwand (Mitte der Schleife 0,21 mm unter der Fläche)
STEP = 0.4              # Abtastung entlang der Schleife


def cs_to_shapely(cs):
    """CrossSection → shapely (Konturen positiv, Löcher negativ orientiert)."""
    polys = [np.asarray(p) for p in cs.to_polygons()]
    outers = [p for p in polys if _area(p) > 0]
    holes = [p for p in polys if _area(p) < 0]
    shp = []
    for o in outers:
        po = Polygon(o)
        hs = [h for h in holes if po.contains(Point(h[0]))]
        shp.append(Polygon(o, hs))
    return unary_union(shp) if shp else MultiPolygon()


def _area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


def d_out(x, y):
    """Abstand zur Außenkontur des Würfels (negativ = innen)."""
    c = M.W / 2
    h = M.W / 2 - M.R
    qx, qy = np.abs(x - c) - h, np.abs(y - c) - h
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - M.R


def sample_loop(p, step=STEP):
    q = np.vstack([p, p[:1]])
    seg = np.diff(q, axis=0)
    ln = np.hypot(seg[:, 0], seg[:, 1])
    pts, lens = [], []
    for a, s, L in zip(q[:-1], seg, ln):
        n = max(1, int(np.ceil(L / step)))
        t = (np.arange(n) + 0.5) / n
        pts.append(a + np.outer(t, s))
        lens.append(np.full(n, L / n))
    return np.vstack(pts), np.concatenate(lens)


def layer_heights(h):
    z, out = FIRST / 2, []
    out.append(z)
    z = FIRST + LAYER / 2
    while z < h:
        out.append(z)
        z += LAYER
    return np.array(out)


def analyse(korpus=None, alt=None, neu=None, verbose=False):
    korpus = korpus or M.korpus()
    alt = alt or MD.ohne_fuzzy()
    neu = neu or MD.aussenhaut()
    z0 = M.BASE_T                                    # Korpus steht im Druck auf z = 0, im Modell auf z = BASE_T
    zs = layer_heights(M.HB - M.BASE_T)
    rows = []
    for i, zp in enumerate(zs):
        z = z0 + zp
        cs = korpus.slice(z)
        if cs.is_empty():
            continue
        ext = cs.offset(-W_EXT / 2, JoinType.Miter)  # Mittellinie der Außenwand
        r_alt = cs_to_shapely(alt.slice(z))
        r_neu = cs_to_shapely(neu.slice(z))
        n_kontur = n_loch = 0
        r = dict(layer=i, z_druck=zp, z_modell=z, innen_alt=0.0, innen_neu=0.0, aussen_alt=0.0, aussen_neu=0.0,
                 front_alt=0.0, front_neu=0.0, kammer_alt=0.0, kammer_neu=0.0)
        for p in ext.to_polygons():
            p = np.asarray(p)
            is_contour = _area(p) > 0
            n_kontur += is_contour
            n_loch += not is_contour
            if not is_contour or i == 0:             # „Kontur“: nur Konturen; erste Schicht ohne
                continue
            pts, ln = sample_loop(p)
            x, y = pts[:, 0], pts[:, 1]
            in_alt = contains_xy(r_alt, x, y) if not r_alt.is_empty else np.zeros(len(x), bool)
            in_neu = contains_xy(r_neu, x, y) if not r_neu.is_empty else np.zeros(len(x), bool)
            fz_alt = ~in_alt                         # A: überall Fuzzy außer im Modifier „ohne“
            fz_neu = in_neu                          # B: nur im Modifier „Außenhaut“
            d = d_out(x, y)
            innen = (d < -1.5) & (y > M.BAY_D + 4.2)  # Innenseite des Korpus (ohne Mulde/Ausschnitt vorne)
            front = (d < -1.5) & ~innen
            aussen = d >= -1.5
            kammer = innen & (y < M.DIV_Y + 3.0 - 0.5)        # Innenseite der Lautsprecherkammer (vorne)
            for key, fz in (("alt", fz_alt), ("neu", fz_neu)):
                r[f"innen_{key}"] += float(ln[fz & innen & ~kammer].sum())
                r[f"kammer_{key}"] += float(ln[fz & kammer].sum())
                r[f"front_{key}"] += float(ln[fz & front].sum())
                r[f"aussen_{key}"] += float(ln[fz & aussen].sum())
        r["konturen"], r["loecher"] = n_kontur, n_loch
        rows.append(r)
        if verbose and i % 50 == 0:
            print(f"  Schicht {i:4d} z {zp:6.1f}: innen alt {r['innen_alt']:7.1f} neu {r['innen_neu']:6.1f}", flush=True)
    return rows


def bands(rows, key, thr=5.0):
    out, cur = [], None
    for r in rows:
        on = r[key] > thr
        if on and cur is None:
            cur = [r["z_druck"], r["z_druck"], r[key]]
        elif on:
            cur[1] = r["z_druck"]
            cur[2] = max(cur[2], r[key])
        elif cur is not None:
            out.append(tuple(cur))
            cur = None
    if cur is not None:
        out.append(tuple(cur))
    return out


if __name__ == "__main__":
    rows = analyse(verbose=True)
    print("\nBänder mit Fuzzy INNEN im Elektronikraum, alter Aufbau (Druckhöhe, z ab Druckplatte, mm):")
    for a, b, mx in bands(rows, "innen_alt"):
        print(f"  {a - LAYER / 2:6.1f} – {b + LAYER / 2:6.1f}   bis {mx:5.0f} mm Innenwand je Schicht")
    print("Bänder mit Fuzzy INNEN in der Lautsprecherkammer, alter Aufbau:")
    for a, b, mx in bands(rows, "kammer_alt"):
        print(f"  {a - LAYER / 2:6.1f} – {b + LAYER / 2:6.1f}   bis {mx:5.0f} mm")
    print("Bänder mit Fuzzy in Lautsprecher-Mulde/Ausschnitt vorne, alter Aufbau:")
    for a, b, mx in bands(rows, "front_alt"):
        print(f"  {a - LAYER / 2:6.1f} – {b + LAYER / 2:6.1f}   bis {mx:5.0f} mm")
    ni = sum(r["innen_neu"] + r["front_neu"] + r["kammer_neu"] for r in rows)
    print(f"\nNeuer Aufbau: Fuzzy innen gesamt {ni:.1f} mm (Soll 0)")
    da = np.array([r["aussen_alt"] for r in rows]); dn = np.array([r["aussen_neu"] for r in rows])
    diff = [(r["z_druck"], r["aussen_alt"], r["aussen_neu"]) for r in rows if abs(r["aussen_alt"] - r["aussen_neu"]) > 3]
    print(f"Außen: alt {da.mean():.0f} mm/Schicht, neu {dn.mean():.0f} mm/Schicht; Schichten mit Unterschied > 3 mm: {len(diff)}")
    for z, a, n in diff[:12]:
        print(f"   z {z:6.1f}: alt {a:6.0f}  neu {n:6.0f}")
    if ni > 1.0:
        sys.exit("FEHLER: neuer Aufbau verfuzzt innen")


def bild(rows, z_schnitt=54.1, fn="fuzzy_analyse.png"):
    """Bild: Schnitt durch eine Schicht im Band (alt/neu) + Fuzzy-Länge innen über der Druckhöhe."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    korpus, alt, neu = M.korpus(), MD.ohne_fuzzy(), MD.aussenhaut()
    z = M.BASE_T + z_schnitt
    cs = korpus.slice(z)
    ext = cs.offset(-W_EXT / 2, JoinType.Miter)
    r_alt, r_neu = cs_to_shapely(alt.slice(z)), cs_to_shapely(neu.slice(z))
    fig = plt.figure(figsize=(15, 9.6), dpi=110)
    gs = GridSpec(2, 2, height_ratios=[1.25, 1], hspace=0.28, wspace=0.08)
    for k, (titel, reg, modus) in enumerate((("Gedruckt (alt): Objekt „Kontur“, Modifier 01m „ohne Fuzzy“", r_alt, "alt"),
                                             ("Neu: Objekt „Deaktiviert“, Modifier 01f „Kontur“ (1 mm Außenhaut)", r_neu, "neu"))):
        ax = fig.add_subplot(gs[0, k])
        for p in cs.to_polygons():
            p = np.asarray(p)
            ax.fill(p[:, 0], p[:, 1], color="#e9dcc3", lw=0)
        for p in cs.to_polygons():
            p = np.vstack([np.asarray(p), np.asarray(p)[:1]])
            ax.plot(p[:, 0], p[:, 1], color="#b9a888", lw=0.5)
        grau, rot = [], []
        for p in ext.to_polygons():
            p = np.asarray(p)
            contour = _area(p) > 0
            pts, _ = sample_loop(p, 0.3)
            inside = contains_xy(reg, pts[:, 0], pts[:, 1]) if not reg.is_empty else np.zeros(len(pts), bool)
            fz = (~inside if modus == "alt" else inside) & contour
            seg = np.stack([pts, np.roll(pts, -1, axis=0)], axis=1)
            ok = np.hypot(*(seg[:, 1] - seg[:, 0]).T) < 1.0
            grau.append(seg[ok & ~fz]); rot.append(seg[ok & fz])
        from matplotlib.collections import LineCollection
        ax.add_collection(LineCollection(np.vstack(grau), colors="#8a8a8a", linewidths=0.9))
        ax.add_collection(LineCollection(np.vstack(rot), colors="#d62728", linewidths=2.6))
        ax.set_aspect("equal"); ax.set_xlim(-8, 160); ax.set_ylim(-14, 152)
        ax.set_title(titel, fontsize=10.5)
        ax.text(70, 70, "Elektronikraum", ha="center", va="center", fontsize=10, color="#555")
        ax.text(70, 26, "Lautsprecherkammer", ha="center", va="center", fontsize=9, color="#555")
        ax.text(70, -6, "vorne (Lautsprecher-Ausschnitt)", ha="center", va="top", fontsize=9, color="#555")
        ax.text(70, 146, "hinten (Lüftung, USB-C)", ha="center", va="bottom", fontsize=9, color="#555")
        ax.text(143, 84, "rechts\n(Drehgeber)", ha="left", va="center", fontsize=8.5, color="#555")
        ax.text(-3, 70, "links", ha="right", va="center", fontsize=8.5, color="#555", rotation=90)
        ax.axis("off")
    fig.text(0.5, 0.955, f"Draufsicht auf die Schicht bei {z_schnitt:.1f} mm Druckhöhe – rot = Außenwand-Linie bekommt Fuzzy, grau = glatt",
             ha="center", fontsize=12)
    ax = fig.add_subplot(gs[1, :])
    zz = np.array([r["z_druck"] for r in rows])
    ie = np.array([r["innen_alt"] for r in rows]); ik = np.array([r["kammer_alt"] for r in rows])
    ax.fill_between(zz, 0, ie, color="#d62728", alpha=0.85, step="mid", label="alt: Innenseite Elektronikraum")
    ax.fill_between(zz, ie, ie + ik, color="#ff9896", alpha=0.9, step="mid", label="alt: Innenseite Lautsprecherkammer")
    neu_i = np.array([r["innen_neu"] + r["kammer_neu"] for r in rows])
    ax.plot(zz, neu_i, color="#2ca02c", lw=2.2, label="neu: Innenseite (überall 0)")
    ax.set_xlim(0, M.HB - M.BASE_T); ax.set_ylim(0, 720)
    ax.set_xlabel("Druckhöhe ab Druckplatte (mm)"); ax.set_ylabel("Innenwand mit Fuzzy je Schicht (mm)")
    for a, b, txt in ((16.8, 23.2, "Klinke"), (29.6, 103.4, "Lautsprecher-Ausschnitt (nur Kammer)"),
                      (46.0, 62.0, "Lüftung, USB-C, Drehgeber"), (110.0, 122.4, "Riemen, Deckelschrauben")):
        ax.annotate(txt, ((a + b) / 2, 690 if txt.startswith("Laut") else 610), ha="center", fontsize=9)
    ax.axvline(z_schnitt, color="#444", ls=":", lw=1)
    ax.legend(loc="upper left", bbox_to_anchor=(0.66, 0.78), fontsize=9, frameon=True, framealpha=0.9)
    ax.grid(alpha=0.25)
    ax.set_title("Wo der Slicer innen Fuzzy aufträgt – jede Bandkante ist eine Stelle, an der sich die Schichtzeit sprunghaft ändert",
                 fontsize=10.5)
    fig.savefig(_os.path.join(OUTDIR, fn), bbox_inches="tight")
    return _os.path.join(OUTDIR, fn)


if __name__ == "__main__" and "--bild" in sys.argv:
    print(bild(rows))
