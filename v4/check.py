"""Kollisions- und Druckbarkeitscheck für Musikbox v4."""
import itertools, math, numpy as np
from manifold3d import Manifold
import model as M

BED = (256.0, 256.0, 256.0)


def inter_vol(a, b):
    if a.is_empty() or b.is_empty():
        return 0.0
    ab, bb = a.bounding_box(), b.bounding_box()
    if any(ab[i] > bb[i + 3] or bb[i] > ab[i + 3] for i in range(3)):
        return 0.0
    return (a ^ b).volume()


def collisions(parts, ph):
    items = [(k, v, "Druckteil") for k, v in parts.items()] + [(k, v, "Bauteil") for k, v in ph.items()]
    allowed = {frozenset(p) for p in [("deckel_orange", "deckel_beige"), ("deckel_orange", "ein_taste"), ("deckel_beige", "ein_taste"),
                                       ("deckelrahmen", "ein_taste"), ("RC522", "RC522-Stecker (Zone)"),
                                       ("Klinkenstecker am Pi (Zone)", "USB-C-Stecker am Akku-Board (Zone)"),
                                       ("Klinkenstecker am Pi (Zone)", "Kabel Klemmreihe hinten (Zone)")]}
    out = []
    for (ka, a, ta), (kb, b, tb) in itertools.combinations(items, 2):
        if frozenset((ka, kb)) in allowed:
            continue
        v = inter_vol(a, b)
        if v > 0.5:
            out.append((ka, kb, v))
    return out


def gaps(ph, parts):
    """Wichtige Abstände (mm)."""
    g = {}
    g["Oberkante Klemmen (z)"] = ph["Pi + Klemmen-Aufsatz"].bounding_box()[5]
    g["Unterkante Kartenfach (z)"] = parts["kartenfach"].bounding_box()[2]
    g["Unterkante Klemmen im Deckel (z)"] = min(ph[k].bounding_box()[2] for k in ("WAGO GND B", "WAGO 3,3 V", "WAGO SCL", "Touch-Modul MPR121"))
    for a, b in (("Pi + Klemmen-Aufsatz", "kartenfach"), ("Pi + Klemmen-Aufsatz", "RC522"), ("Klinkenstecker am Pi (Zone)", "korpus"),
                 ("Pi + Klemmen-Aufsatz", "WAGO GND B"), ("Pi + Klemmen-Aufsatz", "Touch-Modul MPR121"),
                 ("Akku-Board mit Zellen", "korpus"), ("Kabel Klemmreihe links (Zone)", "korpus"), ("Kabel Klemmreihe rechts (Zone)", "Drehgeber"),
                 ("Kabel Klemmreihe hinten (Zone)", "USB-C-Einbaubuchse mit Kabel"), ("USB-C-Stecker am Akku-Board (Zone)", "korpus"),
                 ("WAGO GND A", "korpus"), ("Verstärker", "korpus"), ("boden", "korpus"), ("Lautsprecher", "korpus"),
                 ("Kurzhubtaster", "kartenfach"), ("RC522", "deckelrahmen"), ("RC522-Stecker (Zone)", "korpus"), ("RC522-Stecker (Zone)", "deckelrahmen"), ("RC522-Stecker (Zone)", "kartenfach"), ("Touch-Modul MPR121", "kartenfach")):
        A = ph.get(a, parts.get(a)); B = ph.get(b, parts.get(b))
        g[f"Abstand {a} ↔ {b}"] = A.min_gap(B, 40.0)
    return g


# --- Druckausrichtung ---
def orient(name, m):
    """Gibt das Teil so zurück, wie es auf der Platte liegt (z=0 unten)."""
    if name in ("korpus", "boden", "deckel_orange", "deckel_beige", "riemen_gegenplatte_flat"):
        pass
    if name == "deckelrahmen":
        m = m.mirror([0, 0, 1])                       # Deckelseite nach unten
    elif name == "kartenfach":
        # Vorderwand auf die Platte: lokale -w nach unten
        F = M.card_frame()
        R = F[:, :3]
        inv = np.eye(4); inv[:3, :3] = R.T; inv[:3, 3] = -R.T @ F[:, 3]
        m = m.transform(inv[:3, :].astype(np.float32))   # zurück in Kartenkoordinaten (u, v, w)
        m = m.rotate([0, -90, 0])                        # auf die Seite: u senkrecht, Kartenschacht wird senkrechter Schlitz
    elif name == "stoffrahmen":
        m = m.rotate([90, 0, 0])                         # Front nach unten, Stifte nach oben
    elif name == "drehknopf":
        m = m.rotate([0, 90, 0])                         # Stirnfläche nach unten
    elif name == "ein_taste":
        m = m.mirror([0, 0, 1])                          # Kopf nach unten
    elif name == "riemen_gegenplatte":
        m = m.rotate([0, 90, 0])
    bb = m.bounding_box()
    return m.translate([-bb[0], -bb[1], -bb[2]])


def overhangs(m, limit_deg=45.0, bed_tol=0.25):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    n = np.cross(b - a, c - a)
    area = np.linalg.norm(n, axis=1) / 2
    nz = n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
    zc = (a[:, 2] + b[:, 2] + c[:, 2]) / 3
    bad = (nz < -math.cos(math.radians(limit_deg)) - 0.01) & (zc > bed_tol) & (area > 1e-6)
    # Gruppen nach Höhe
    groups = {}
    for i in np.where(bad)[0]:
        key = round(zc[i] * 2) / 2
        g = groups.setdefault(key, [0.0, [1e9, 1e9, -1e9, -1e9]])
        g[0] += area[i]
        pts = np.vstack([a[i], b[i], c[i]])
        g[1] = [min(g[1][0], pts[:, 0].min()), min(g[1][1], pts[:, 1].min()), max(g[1][2], pts[:, 0].max()), max(g[1][3], pts[:, 1].max())]
    return area[bad].sum(), groups


def insertion_top(parts, ph):
    """Deckel mit Rahmen, Kartenfach, Taste und Deckel-Modulen geht von oben an der (ringsum geschlossenen) Auflage vorbei."""
    from manifold3d import JoinType
    free = M.slab(M.INN.offset(-M.LEDGE - 0.2, JoinType.Round), -10, M.HB + 10)
    res = {}
    for k in ("deckelrahmen", "kartenfach", "ein_taste"):
        res[k] = (parts[k] - free).volume()
    for k in M.LID_PH:
        if k != "Karte (gesteckt)":
            res[k] = (ph[k] - free).volume()
    return res


def sweep_down(m):
    """Raum, den ein Teil beim Hochschieben von unten überstreicht (Grundriss bis zur Oberkante)."""
    bb = m.bounding_box()
    return M.slab(m.project(), -300, bb[5])


def insertion_bottom(parts, ph):
    """Boden mit allem, was darauf sitzt, wird von unten eingeschoben. Nichts darf dabei an Korpus, Wandteilen oder Deckel hängen bleiben."""
    above = M.box(-50, -50, M.BASE_T + 0.05, 250, 250, 300)
    fixed = M.U([parts["korpus"] ^ above, parts["riemen_gegenplatte"], parts["deckelrahmen"], parts["kartenfach"],
                 parts["deckel_orange"], parts["ein_taste"]] + [ph[k] for k in M.WALL_PH + M.LID_PH])
    res = {"boden (Aufbauten)": inter_vol(sweep_down(parts["boden"] ^ above), fixed)}
    for k in M.BASE_PH:
        res[k] = inter_vol(sweep_down(ph[k]), fixed)
    return res


if __name__ == "__main__":
    parts = M.build()
    ph = M.placeholders()
    print("== Deckelteile von oben (Volumen außerhalb der Auflage, soll 0) ==")
    for k, v in insertion_top(parts, ph).items():
        print(f"  {k}: {v:.1f} mm³")
    print("== Boden von unten (Hubweg, soll 0) ==")
    for k, v in insertion_bottom(parts, ph).items():
        print(f"  {k}: {v:.1f} mm³")
    print("== Kollisionen ==")
    for a, b, v in collisions(parts, ph):
        print(f"  {a} × {b}: {v:.1f} mm³")
    print("== Abstände ==")
    for k, v in gaps(ph, parts).items():
        print(f"  {k}: {v:.1f}")
    print("== Druck ==")
    for k, m in parts.items():
        o = orient(k, m)
        bb = o.bounding_box()
        tot, groups = overhangs(o)
        print(f"  {k}: {bb[3]:.1f} × {bb[4]:.1f} × {bb[5]:.1f} mm, Überhang {tot:.0f} mm²")
        for z, (ar, xy) in sorted(groups.items(), key=lambda t: -t[1][0])[:6]:
            if ar > 3:
                print(f"      z={z:6.1f}  {ar:7.1f} mm²  Bereich {xy[2]-xy[0]:.1f} × {xy[3]-xy[1]:.1f}")
