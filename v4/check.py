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
    allowed = {frozenset(p) for p in [("deckel_orange", "deckel_beige"), ("gitter_beige", "gitter_logo"), ("deckel_orange", "ein_taste"), ("deckel_beige", "ein_taste"),
                                       ("deckelrahmen", "ein_taste"), ("RC522", "RC522-Stecker (Zone)"),
                                       ("niederhalter", "Pi + Klemmen-Aufsatz"),
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
                 ("Kabel Klemmreihe hinten (Zone)", "USB-C-Platine mit Buchse und Kabeln"), ("USB-C-Stecker am Akku-Board (Zone)", "korpus"),
                 ("WAGO GND A", "korpus"), ("Verstärker", "korpus"), ("boden", "korpus"), ("Lautsprecher", "korpus"), ("Lautsprecher", "gitter_beige"),
                 ("Kurzhubtaster", "kartenfach"),
                 ("niederhalter", "kartenfach"), ("niederhalter", "deckelrahmen"), ("niederhalter", "korpus"), ("niederhalter", "RC522-Stecker (Zone)"),
                 ("niederhalter", "Touch-Modul MPR121"), ("niederhalter", "WAGO GND B"), ("RC522", "deckelrahmen"), ("RC522-Stecker (Zone)", "korpus"), ("RC522-Stecker (Zone)", "deckelrahmen"), ("RC522-Stecker (Zone)", "kartenfach"), ("Touch-Modul MPR121", "kartenfach")):
        A = ph.get(a, parts.get(a)); B = ph.get(b, parts.get(b))
        g[f"Abstand {a} ↔ {b}"] = A.min_gap(B, 40.0)
    # Schraubblock hinten rechts am Deckelrahmen (x = LS_X[1]) getrennt, sonst verdeckt der Tasterhalter den Wert
    x = M.LS_X[1]
    blk = parts["deckelrahmen"] ^ M.box(x - 8, M.W - M.WALL - 2.4 - 0.4 - 10.5, M.LS_BLOCK_Z0 - 1, x + 8, M.W, M.LID_BOT)
    g["Abstand RC522-Stecker (Zone) ↔ Schraubblock Deckelrahmen hinten"] = ph["RC522-Stecker (Zone)"].min_gap(blk, 40.0)
    return g


def symbol_gaps():
    """Abstand jedes Symbols zur Innenkante seiner Ringnut (Probedruck 27.10.: Dreiecke lagen auf der Nut)."""
    from manifold3d import CrossSection
    sym = M.pad_symbols(rings=False)
    out = {}
    for name, (x, y, d) in M.PADS.items():
        part = sym ^ CrossSection.circle(d / 2, M.SEG).translate([x, y])
        out[name] = d / 2 - M.PAD_RING - M._cs_radius(part, x, y)
    return out


# --- Druckausrichtung ---


def gitter_pruefung(parts=None):
    """Gitter (einfarbig) und Logo-Buchstaben (eigene Teile): Schichtanalyse in Druckausrichtung (Stege schmaler als 1 bzw.
    2 Linienbreiten), offene Fläche vor dem Lautsprecher, Luft hinter dem Gitter, Sitz der Buchstaben-Stifte."""
    from manifold3d import CrossSection, JoinType, OpType
    b = parts["gitter_beige"] if parts else M.gitter()[0]
    o = parts["gitter_logo"] if parts else M.gitter()[1]
    B, O = M.gitter_druck(b, b), M.buchstaben_druck(o)
    def thin(cs, r):
        return (cs - cs.offset(-r, JoinType.Round).offset(r, JoinType.Round)).area()
    def rows_of(m):
        out, z, top = [], 0.1, m.bounding_box()[5]
        while z < top:
            cs = m.slice(z)
            out.append(dict(z=z, flaeche=cs.area(), d04=thin(cs, 0.2), d08=thin(cs, 0.42)))
            z += 0.2
        return out
    d, _ = M.GR_HOLE
    pts = M.gitter_holes()
    H = CrossSection.batch_boolean([CrossSection.circle(d / 2, 32).translate([x, z]) for x, z in pts], OpType.Add)
    cone = CrossSection.circle(M.SPK_CUT / 2, 96).translate([M.SPK_X, M.SPK_Z])
    lp = O.decompose()
    gaps = [a_.min_gap(b_, 20) for i, a_ in enumerate(lp) for b_ in lp[i + 1:]]
    return dict(rows=rows_of(B), rows_b=rows_of(O), loecher=len(pts),
                offen_direkt=100 * (H ^ cone).area() / cone.area(),
                offen_mulde=100 * (H ^ M.gitter_bay_cs()).area() / cone.area(),
                luft=M.GR_PLENUM + (M.BAY_D - M.SPK_FLANGE - M.SEAT_D),
                teile=len(lp), abstand_platte=min(gaps), platte=O.bounding_box(),
                stifte=sum(len(M.gitter_stifte(c)) for c in M.gitter_buchstaben_cs()),
                sitz=(b ^ o).volume())


def handedness(name):
    """+1 = Druckausrichtung ist eine reine Drehung, -1 = Spiegelung (Teil käme seitenverkehrt aus dem Drucker).
    Prüfkörper: vier verschieden große Würfel an bekannten Stellen, nach orient() wiedergefunden."""
    sizes = (1.0, 2.0, 3.0, 4.0)
    pos = ((0, 0, 0), (30, 0, 0), (0, 30, 0), (0, 0, 30))
    probe = M.U([M.box(x, y, z, x + s, y + s, z + s) for s, (x, y, z) in zip(sizes, pos)])
    comps = sorted(orient(name, probe).decompose(), key=lambda c: c.volume())
    c = [np.array(k.bounding_box()[:3]) + np.array(k.bounding_box()[3:]) for k in comps]
    c0 = [np.array(p) * 2 + s for s, p in zip(sizes, pos)]
    d1 = np.linalg.det(np.array([c[i] - c[0] for i in (1, 2, 3)]))
    d0 = np.linalg.det(np.array([c0[i] - c0[0] for i in (1, 2, 3)]))
    return int(np.sign(d1 * d0))
def orient(name, m):
    """Gibt das Teil so zurück, wie es auf der Platte liegt (z=0 unten)."""
    if name in ("korpus", "boden", "riemen_gegenplatte_flat", "gummiecken", "eckhuelsen"):
        pass                                          # Gummiecken und Hülsen: wie im Einbau, Fuß bzw. Bund unten
    if name in ("deckel_orange", "deckel_beige"):
        m = m.rotate([0, 180, 0])                     # kopfüber: Oberseite auf die Platte (wie M.deckel_kopfueber)
    elif name == "deckelrahmen":
        m = m.rotate([180, 0, 0])                     # Deckelseite nach unten (gedreht, NICHT gespiegelt)
    elif name == "kartenfach":
        # Vorderwand auf die Platte: lokale -w nach unten
        F = M.card_frame()
        R = F[:, :3]
        inv = np.eye(4); inv[:3, :3] = R.T; inv[:3, 3] = -R.T @ F[:, 3]
        m = m.transform(inv[:3, :].astype(np.float32))   # zurück in Kartenkoordinaten (u, v, w)
        m = m.rotate([0, -90, 0])                        # auf die Seite: u senkrecht, Kartenschacht wird senkrechter Schlitz
    elif name == "gitter_beige":
        m = m.rotate([90, 0, 180])                       # Vorderfläche auf die Platte, Oberkante nach hinten (wie M.gitter_druck)
    elif name == "gitter_logo":
        m = m.rotate([90, 0, 0])                         # Sichtseite auf die Platte, Stifte oben, Unterkante hinten (wie M.buchstaben_druck)
    elif name == "drehknopf":
        m = m.rotate([0, 90, 0])                         # Stirnfläche nach unten
    elif name == "ein_taste":
        m = m.rotate([180, 0, 0])                        # Kopf nach unten (gedreht, nicht gespiegelt)
    elif name == "riemen_gegenplatte":
        m = m.rotate([0, 90, 0])
    elif name == "niederhalter":
        m = m.rotate([180, 0, 0])                        # Dachoberseite (mit Senkungen) auf die Platte, Säulen nach oben
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
    res = {"boden (Aufbauten)": inter_vol(sweep_down(parts["boden"] ^ above), fixed),
           "niederhalter": inter_vol(sweep_down(parts["niederhalter"]), fixed)}
    for k in M.BASE_PH:
        res[k] = inter_vol(sweep_down(ph[k]), fixed)
    return res


def gummiecken_pruefung(parts):
    """Gummiecken (vier einzelne, verschraubt): sitzen ohne Überschneidung auf Korpus und Boden, Hülsen liegen am Boden an und
    berühren das TPU nicht, Abstand zur Fase des Gittersitzes, Rastwulst unter der Fuge, Schraubenlänge, Wandstärken."""
    from manifold3d import JoinType
    g, h = parts["gummiecken"], parts["eckhuelsen"]
    r = {"teile": len(g.decompose()), "volumen_ecke": M.gummiecke().volume(), "volumen_huelse": M.eckhuelse().volume()}
    r["ueberschneidung_korpus"] = inter_vol(g, parts["korpus"])
    r["ueberschneidung_boden"] = inter_vol(g, parts["boden"])
    r["huelse_boden"] = inter_vol(h, parts["boden"])
    r["huelse_anlage"] = h.min_gap(parts["boden"], 1.0)                      # 0 = liegt an
    r["huelse_tpu"] = h.min_gap(g, 2.0)
    sx0, sx1, sz0, sz1 = M.SEAT
    c = M.SEAT_CH
    seat = M.ext_xz(M.rr(sx0 - c, sz0 - c, sx1 + c, sz1 + c, M.SEAT_R + c), -5, 0.5)
    r["abstand_gittersitz"] = g.min_gap(seat, 20.0)
    band = M.slab(M.OUT.offset(-0.05, JoinType.Round) - M.OUT.offset(-1.0, JoinType.Round), M.BASE_T - M.EDGE_V, M.BASE_T)
    r["wulst_volumen"] = (g ^ band).volume()
    # Schraube: Kopf bündig in der Hülse, Spitze im Kernloch des Doms (12 tief ab Boden-Oberseite)
    hd = M.ECK_HUELSE
    z_kopf = -M.ECK_FUSS + hd["luft_unten"]
    r["einschraubtiefe"] = z_kopf + M.ECK_SCHRAUBE - M.BASE_T
    r["kernloch_rest"] = (M.BASE_T + 12.0) - (z_kopf + M.ECK_SCHRAUBE)
    # Wandstärken an der Hülse: Abstand Eckschraube ↔ Außenrundung, TPU unten zwischen Aussparung und Außenfläche, Hülsenwand am Kopf
    (x, y) = M.BASE_BOSSES[0]
    a = M.R - math.hypot(M.R - x, M.R - y)
    r["tpu_unten"] = a - (hd["d_bund"] / 2 + hd["spiel"]) + (M.ECK_WAND - M.ECK_KANTE)
    r["huelse_wand"] = (hd["d_bund"] - M.CSK[0]) / 2
    r["druck_ecke"] = M.gummiecken_druck(M.gummiecke()).bounding_box()
    return r


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
    print("== Symbole auf den Touchfeldern (Abstand zur Ringnut, soll ≥ SYM_GAP) ==")
    for k, v in symbol_gaps().items():
        print(f"  {k}: {v:.2f} mm" + ("" if v >= M.SYM_GAP - 0.01 else "  ZU KNAPP"))
    print("== Druckausrichtung ohne Spiegelung (soll überall +1) ==")
    bad = [k for k in parts if handedness(k) < 0]
    print("  ok" if not bad else "  GESPIEGELT: " + ", ".join(bad))
    print("== Druck ==")
    for k, m in parts.items():
        if k == "deckel_beige":
            continue
        if k == "deckel_orange":                     # beide Deckelteile liegen aufeinander: zusammen prüfen
            k, m = "deckel (02a + 02b zusammen, kopfüber)", parts["deckel_orange"] + parts["deckel_beige"]
            o = orient("deckel_orange", m)
        else:
            o = orient(k, m)
        bb = o.bounding_box()
        tot, groups = overhangs(o)
        print(f"  {k}: {bb[3]:.1f} × {bb[4]:.1f} × {bb[5]:.1f} mm, Überhang {tot:.0f} mm²")
        for z, (ar, xy) in sorted(groups.items(), key=lambda t: -t[1][0])[:6]:
            if ar > 3:
                print(f"      z={z:6.1f}  {ar:7.1f} mm²  Bereich {xy[2]-xy[0]:.1f} × {xy[3]-xy[1]:.1f}")
    print("== Gitter und Logo-Buchstaben (Schichtanalyse in Druckausrichtung) ==")
    g = gitter_pruefung(parts)
    print(f"  {g['loecher']} Löcher; offen direkt vor der Öffnung Ø {M.SPK_CUT:g}: {g['offen_direkt']:.0f} %, über die ganze Mulde: {g['offen_mulde']:.0f} % der Öffnung")
    print(f"  Luft hinter dem Gitter über der Mulde: {g['luft']:.1f} mm")
    r1 = g["rows"][0]
    print(f"  Gitter Schicht 1: {r1['flaeche']:.0f} mm², schmaler als 0,4: {r1['d04']:.2f} mm², als 0,84: {r1['d08']:.2f} mm²")
    back = [r for r in g["rows"] if M.GR_T - M.GR_PLENUM < r["z"] < M.GR_T]
    print(f"  Gitter hinten (Luftraum-Schichten): schmaler als 0,4 höchstens {max(r['d04'] for r in back):.2f} mm² je Schicht")
    b1 = g["rows_b"][0]
    print(f"  Buchstaben: {g['teile']} Teile, {g['stifte']} Stifte, Abstand auf der Platte mindestens {g['abstand_platte']:.1f} mm, "
          f"Platte {g['platte'][3]:.0f} × {g['platte'][4]:.0f} mm; Schicht 1: {b1['flaeche']:.0f} mm², schmaler als 0,4: {b1['d04']:.2f} mm²")
    print(f"  Stifte im Gitter: Überschneidung {g['sitz']:.3f} mm³ (soll 0)")
    print("== Gummiecken (4 einzelne, verschraubt, PETG-Hülsen) ==")
    gp = gummiecken_pruefung(parts)
    d = gp["druck_ecke"]
    print(f"  {gp['teile']} Ecken je {gp['volumen_ecke'] / 1000:.2f} cm³ ≈ {gp['volumen_ecke'] / 1000 * 1.21:.1f} g TPU (Druckmaß {d[3] - d[0]:.1f} × "
          f"{d[4] - d[1]:.1f} × {d[5] - d[2]:.1f} mm); Hülse {gp['volumen_huelse']:.0f} mm³ PETG")
    print(f"  Überschneidung Ecken mit Korpus / Boden: {gp['ueberschneidung_korpus']:.2f} / {gp['ueberschneidung_boden']:.2f} mm³ (soll 0)")
    print(f"  Hülse ∩ Boden {gp['huelse_boden']:.2f} mm³, Abstand zum Boden {gp['huelse_anlage']:.2f} (soll 0 = liegt an), Luft zum TPU {gp['huelse_tpu']:.2f} mm")
    print(f"  Abstand zur Fase des Gittersitzes: {gp['abstand_gittersitz']:.2f} mm (soll ≥ 1)" + ("" if gp['abstand_gittersitz'] >= 1.0 else "  ZU KNAPP"))
    print(f"  Rastwulst unter der Fuge: {gp['wulst_volumen']:.1f} mm³ (soll > 0)")
    print(f"  Schraube 3,0 × {M.ECK_SCHRAUBE:g}: {gp['einschraubtiefe']:.1f} mm im Dom, Kernloch noch {gp['kernloch_rest']:.1f} mm tiefer"
          + ("" if gp['kernloch_rest'] > 0.3 else "  ZU LANG"))
    print(f"  TPU unten zwischen Hülsenaussparung und Außenfläche: {gp['tpu_unten']:.2f} mm; Hülsenwand am Kopf {gp['huelse_wand']:.2f} mm")
    print("== Fuzzy Skin (Nachbildung ElegooSlicer je 0,2-mm-Schicht, Modifier 01f Außenhaut) ==")
    import fuzzy_check as FC
    rows = FC.analyse(korpus=parts["korpus"])
    innen = sum(r["innen_neu"] + r["kammer_neu"] + r["front_neu"] for r in rows)
    aussen = [r["aussen_neu"] for r in rows if FC.LAYER < r["z_druck"] < M.FUZZ_Z[1] - M.BASE_T - FC.LAYER and r["z_druck"] > M.FUZZ_Z[0] - M.BASE_T]
    print(f"  innen mit Fuzzy: {innen:.1f} mm (soll 0)" + ("" if innen < 1 else "  FEHLER"))
    print(f"  außen mit Fuzzy: {min(aussen):.0f}–{max(aussen):.0f} mm je Schicht (Fasen unten/oben glatt)")
    print("  alter Aufbau (01m ohne Fuzzy) hätte innen: " +
          ", ".join(f"{a - FC.LAYER / 2:.1f}–{b + FC.LAYER / 2:.1f}" for a, b, _ in FC.bands(rows, "innen_alt")) + " mm Druckhöhe")
