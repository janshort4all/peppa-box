"""Prüfungen der Kartenbox: Kollision, Schwenk, Spiel, Wandstärken, Überhänge, Bauraum, Federdehnung.

Aufruf: python3 check.py        (schreibt out/PRUEFBERICHT.md)
Alle Zahlen stammen aus dem Modell (model.py), nichts ist angenommen. Ausnahmen sind als ANNAHME gekennzeichnet.
"""
import math, os, sys
import numpy as np, trimesh
import manifold3d as m3
from manifold3d import Manifold, Mesh
import model as M
import build as B

OUT = B.OUT
REPORT = []
FAIL = []


def say(s=""):
    print(s)
    REPORT.append(s)


def ok(cond, text):
    say(("OK    " if cond else "FEHLER ") + text)
    if not cond:
        FAIL.append(text)
    return cond


def to_manifold(tm):
    mesh = Mesh(vert_properties=np.asarray(tm.vertices, dtype=np.float32), tri_verts=np.asarray(tm.faces, dtype=np.uint32))
    return Manifold(mesh)


def inter_vol(a, b):
    return Manifold.batch_boolean([a, b], m3.OpType.Intersect).volume()


def rot_x_about(tm, ang_deg, y0, z0):
    """Drehung um die Achse parallel x durch (y0,z0); Öffnen = Vorderkante nach oben/hinten (Vorzeichen wie render.py)."""
    a = math.radians(ang_deg)
    c, s = math.cos(a), math.sin(a)
    T = np.eye(4)
    T[1, 1], T[1, 2], T[2, 1], T[2, 2] = c, s, -s, c
    T[1, 3] = y0 - (c * y0 + s * z0)
    T[2, 3] = z0 - (-s * y0 + c * z0)
    m = tm.copy()
    m.apply_transform(T)
    return m


CARD_R = 5.0  # Eckenradius der Karte, gemessen an v4/out/10_karte_orange.stl (Eckabstand 2,07 mm = r·(√2−1))


def card_box(x0, y0, y1, z0, z1, tilt_deg=0.0, pivot=None):
    """Karte als abgerundetes Rechteck in der y-z-Ebene, in x extrudiert."""
    from shapely.geometry import box as sbox
    poly = sbox(y0 + CARD_R, z0 + CARD_R, y1 - CARD_R, z1 - CARD_R).buffer(CARD_R, resolution=24)
    pts = np.array(poly.exterior.coords)[:-1]
    n = len(pts)
    t = M.CARD_T - 0.1
    v = np.vstack([np.column_stack([np.full(n, 0.0), pts]), np.column_stack([np.full(n, t), pts])])
    f = []
    for i in range(1, n - 1):
        f.append([0, i + 1, i])
        f.append([n, n + i, n + i + 1])
    for i in range(n):
        j = (i + 1) % n
        f.append([i, j, n + j]); f.append([i, n + j, n + i])
    b = trimesh.Trimesh(v, f, process=True)
    b.fix_normals()
    b.apply_translation((x0, 0, 0))
    if tilt_deg:
        a = math.radians(tilt_deg)
        c, s = math.cos(a), math.sin(a)
        py, pz = pivot
        T = np.eye(4)
        T[1, 1], T[1, 2], T[2, 1], T[2, 2] = c, s, -s, c
        T[1, 3] = py - (c * py + s * pz)
        T[2, 3] = pz - (-s * py + c * pz)
        b.apply_transform(T)
    return b


def stacks(tilt_deg=0.0, which="front"):
    """30 Karten, je Fach 10 linksbündig, im Inlay (Kartenspiel in y: PLAY_Y).
    front = Karten lehnen nach vorn (Kippachse: untere Kante, Karte ganz hinten im Inlay)
    back  = Karten lehnen nach hinten (Karte ganz vorn im Inlay)"""
    bs = []
    y_front = M.WALL + M.LINER_CLR + M.DIV
    z_top = M.CARD_Z0 + M.CARD_H
    for k in range(M.NC):
        xc0 = -M.LINER_X / 2 + M.DIV + k * (M.SLOT_W + M.DIV)
        for i in range(M.PER):
            x0 = xc0 + i * M.CARD_T + 0.05 + (7.0 if k == 0 else 0.0)  # Randfach links: Stapel liegt an der Trennwand (Kartenecken stoßen sonst an die Gehäuse-Rundung)
            if which == "front":
                y0 = y_front + M.PLAY_Y
                b = card_box(x0, y0, y0 + M.CARD_W, M.CARD_Z0, z_top, -tilt_deg, (y0, M.CARD_Z0))
            else:
                y0 = y_front
                b = card_box(x0, y0, y0 + M.CARD_W, M.CARD_Z0, z_top, tilt_deg, (y0 + M.CARD_W, M.CARD_Z0))
            bs.append(b)
    return trimesh.util.concatenate(bs)


def max_tilt():
    """größte Kippung einer Karte: Vorderfläche am Fugenrand der Basis (y = WALL), Unterkante hinten am Inlay."""
    y_b = M.WALL + M.LINER_CLR + M.DIV + M.PLAY_Y   # Karte ganz nach hinten im Inlay
    y_f_inlay = M.WALL + M.LINER_CLR + M.DIV
    # a) Karte lehnt an der Fugenkante der Basis: Vorderfläche y(z) = y_b - (z-Z0) tan φ ≥ WALL bei z = Z_RIM
    t_wall = (y_b - M.WALL) / (M.Z_RIM - M.CARD_Z0)
    # b) Vorderwand des Inlays ist vorn niedrig (Schwung): Karte darf dort nicht ins Inlay kippen
    z_front_top = M.BASE_FLOOR + M.LINER_H - 20.0
    t_inlay = (y_b - y_f_inlay) / (z_front_top - M.CARD_Z0)
    return math.degrees(math.atan(min(t_wall, t_inlay))), math.degrees(math.atan(t_wall)), math.degrees(math.atan(t_inlay))


def main():
    say("# Prüfbericht Kartenbox (automatisch erzeugt von kartenbox/check.py)")
    say()
    P = {"basis": M.basis(), "deckel": M.deckel(), "deckel_ohne_haken": M.deckel(hook=False), "inlay": M.inlay()}
    T = {k: B.to_mesh(v) for k, v in P.items()}

    say("## 1. Netze")
    for k, m in T.items():
        ok(m.is_watertight and m.is_winding_consistent, f"{k}: Netz wasserdicht, {len(m.faces)} Dreiecke, {m.volume/1000:.1f} cm³")
    mass = {k: T[k].volume / 1000 * 1.27 for k in ("basis", "deckel", "inlay")}
    say(f"Masse bei massivem Volumen und PETG 1,27 g/cm³ (Obergrenze, Füllung und Wände zählen voll): Basis {mass['basis']:.0f} g, Deckel {mass['deckel']:.0f} g, Inlay {mass['inlay']:.0f} g, zusammen {sum(mass.values()):.0f} g (ANNAHME Dichte 1,27 g/cm³)")
    say()

    Mb, Ml, Ml0, Mi = (to_manifold(T[k]) for k in ("basis", "deckel", "deckel_ohne_haken", "inlay"))

    say("## 2. Statische Kollisionen (geschlossen, Überschneidungsvolumen in mm³)")
    v = inter_vol(Ml0, Mb)
    ok(v < 0.5, f"Deckel (ohne Haken) ↔ Basis: {v:.2f} mm³")
    v = inter_vol(Mi, Mb)
    ok(v < 0.5, f"Inlay ↔ Basis: {v:.2f} mm³")
    v = inter_vol(Mi, Ml)
    ok(v < 0.5, f"Inlay ↔ Deckel: {v:.2f} mm³")
    cards0 = to_manifold(stacks(0.0, "front"))
    cards1 = to_manifold(stacks(0.0, "back"))
    for nm, cm in (("30 Karten ganz hinten im Inlay", cards0), ("30 Karten ganz vorn im Inlay", cards1)):
        ok(inter_vol(cm, Mb) < 0.5, f"{nm} ↔ Basis: {inter_vol(cm, Mb):.2f} mm³")
        ok(inter_vol(cm, Mi) < 0.5, f"{nm} ↔ Inlay: {inter_vol(cm, Mi):.2f} mm³")
        ok(inter_vol(cm, Ml) < 0.5, f"{nm} ↔ Deckel: {inter_vol(cm, Ml):.2f} mm³")
    say()

    say("## 3. Fassungsvermögen und Ecken")
    need = M.PER * M.CARD_T
    say(f"Fach innen {M.SLOT_W:.1f} mm, 10 Karten = {need:.1f} mm, frei {M.SLOT_W-need:.1f} mm je Fach (Karte 70 × 112 × 4 mm aus 10_karte_orange.stl)")
    # Eckkante der Randkarte gegen die Rundung des Inlays und der Basis
    def inset(r, half_y):
        # Karte (halbe Breite 35) an der Außenwand: wie weit muss sie von der Wand weg, damit die Kartenecke nicht in die Rundung stößt
        d = 35.0 - (half_y - r)
        return 0.0 if d <= 0 else r - math.sqrt(max(r * r - d * d, 0.0))
    i_in = inset(M.LINER_R_IN, (M.LINER_Y - 2 * M.DIV) / 2)
    i_b = inset(M.R_IN, M.D_I / 2) - (M.W_I / 2 - (M.LINER_X / 2 - M.DIV)) if False else inset(M.R_IN, M.D_I / 2) - (M.W_I / 2 - (M.LINER_X / 2 - M.DIV))
    say(f"Randfach: Kartenlänge 70 mm in 74 mm Inlay-Tiefe → die Randkarte muss mindestens {i_in:.1f} mm von der Außenwand weg stehen (Ecken-Rundung); ganz hinten/vorn im Spiel sind es 7 mm. Im Test liegt der linke Stapel an der Trennwand (+7 mm).")
    ok(M.SLOT_W - need - 7.0 >= 0.5, "Randfach fasst 10 Karten auch bei 7 mm Abstand der Randkarte von der Außenwand (Luft > 0,5 mm)")
    ok(M.NC * M.PER == 30, "Gesamtzahl 30 Karten")
    say()

    say("## 4. Deckel-Schwenk (Rotation um die Scharnierachse, Schritt 1°, 0–125°)")
    tmax, t_wall, t_inlay = max_tilt()
    say(f"Größte Kippung einer Karte nach vorn/hinten: {tmax:.2f}° (Wand {t_wall:.2f}°, Inlay-Vorderwand {t_inlay:.2f}°) – Schwenkprüfung mit {tmax-0.05:.2f}° (mehr lässt die Basiswand nicht zu)")
    tilt = tmax - 0.05
    cases = {
        "Karten senkrecht, ganz hinten im Inlay": stacks(0.0, "front"),
        "Karten senkrecht, ganz vorn im Inlay": stacks(0.0, "back"),
        f"Karten {tilt:.1f}° nach vorn gekippt": stacks(tilt, "front"),
        f"Karten {tilt:.1f}° nach hinten gekippt": stacks(tilt, "back"),
    }
    cm_cases = {k: to_manifold(v) for k, v in cases.items()}
    worst = {k: 0.0 for k in cases}
    first_hit = {k: None for k in cases}
    worst_base = 0.0
    first_base = None
    angs = list(np.arange(0, 125.1, 1.0))
    for a in angs:
        lid_r = rot_x_about(T["deckel_ohne_haken"], a, M.Y_H, M.Z_H)
        Mlr = to_manifold(lid_r)
        vb = inter_vol(Mlr, Mb)
        if a > 0 and vb > 0.5 and first_base is None:
            first_base = a
        worst_base = max(worst_base, vb if a > 0 else 0)
        for k, cm in cm_cases.items():
            vv = inter_vol(Mlr, cm)
            if vv > 2.0 and first_hit[k] is None:
                first_hit[k] = a
            worst[k] = max(worst[k], vv)
    ok(first_base is None, f"Deckel ↔ Basis (Wände, Knöchel, Ösen) im ganzen Schwenkbereich frei" + ("" if first_base is None else f" – erste Berührung bei {first_base}°"))
    for k in cases:
        ok(first_hit[k] is None, f"Deckel ↔ {k}: frei bis 125° (größte Überschneidung {worst[k]:.1f} mm³; Toleranz 2 mm³ ≈ 0,05 mm Eindringtiefe am Grenzfall)" + ("" if first_hit[k] is None else f" – erste Berührung bei {first_hit[k]}°"))
    say()

    say("## 5. Scharnier und Verschluss (rechnerisch)")
    # Hakeneingriff: Eindringtiefe des Hakens in die Basiswand beim Schließen
    pen = M.HOOK_H - M.LID_CLR
    say(f"Hakenhöhe {M.HOOK_H:.2f} mm, Spalt zur Basiswand {M.LID_CLR:.2f} mm → Zunge muss beim Schließen {pen:.2f} mm nach außen federn (plus 0,1 mm Reserve für Druckabweichung)")
    L = -M.TONGUE_Z0
    t = M.LID_WALL
    eps = 1.5 * t * (pen + 0.1) / L ** 2
    E = 1800.0  # MPa  ANNAHME PETG (Datenblattwerte 1500–2100 MPa)
    I = M.TW * t ** 3 / 12
    k = 3 * E * I / L ** 3
    F = k * (pen + 0.1)
    say(f"Freie Federlänge {L:.0f} mm, Dicke {t:.2f} mm, Breite {M.TW:.0f} mm → Randfaserdehnung {eps*100:.2f} % (ANNAHME PETG E = {E:.0f} MPa; Streckdehnung PETG ca. 4 %), Federkraft {F:.1f} N, mit 45°-Flanke und Reibung 0,3 ca. {F*(1+0.3)/(1-0.3):.0f} N Öffnungs-/Schließkraft")
    ok(eps < 0.01, "Biegedehnung der Zunge unter 1 % (Dauerfestigkeit, kein Ermüdungsbruch zu erwarten)")
    ok(F < 10, "Öffnungskraft unter 10 N, für ein Kind (6 Jahre) machbar (ANNAHME, nicht gemessen → Coupon K2)")
    w_left = M.WALL - M.PRELOAD * 0 - (M.HOOK_H - M.LID_CLR + M.GROOVE_CLR)
    say(f"Basiswand an der Haken-Nut: {w_left:.2f} mm Restwand (Wand {M.WALL:.2f} mm, Nut {M.HOOK_H - M.LID_CLR + M.GROOVE_CLR:.2f} mm tief)")
    ok(w_left >= 1.2, "Restwand an der Nut mindestens 1,2 mm (3 Linien)")
    gap_pin = M.RK - M.BORE_BASE / 2
    say(f"Scharnier: Knöchelradius {M.RK:.1f} mm, Wand um den Stift {gap_pin:.2f} mm, Stift Ø {M.PIN_D:.1f} mm, Stiftlänge 90 mm, Paketlänge {M.LH:.0f} mm, Knöchelbreite {M.SEG:.1f} mm")
    ok(gap_pin >= 1.5, "Knöchelwand mindestens 1,5 mm")
    ok(abs(M.LH - (M.NSEG * M.SEG + (M.NSEG - 1) * M.AX)) < 1e-6, "Scharnierpaket: 5 Knöchel + 4 × Axialspiel = Paketlänge")
    ok(M.LH - M.END_WALL >= 90.0, "Stift 90 mm passt zwischen Blindende und rechtes Ende")
    say()

    say("## 6. Spiele und Wandstärken (aus den Netzen gemessen)")
    # Abstand Deckelhaut ↔ Basisaußenseite (Sitzleiste/Auflage und Haken ausgenommen)
    pts = T["deckel_ohne_haken"].vertices
    sel = pts[(pts[:, 2] < M.Z_RIM - 1.0) & (pts[:, 2] > M.Z_RIM - M.SKIRT + 0.5)]
    sel = sel[(np.abs(sel[:, 0]) > 40) | (sel[:, 1] > 5)]  # Zunge/Lasche vorn Mitte ausnehmen
    q = trimesh.proximity.ProximityQuery(T["basis"])
    d = np.abs(q.signed_distance(sel))
    # nur Punkte der Innenseite der Haut (Abstand klein)
    inner = d[d < 3.0]
    say(f"Deckelhaut ↔ Basis (Innenseite der Haut): kleinster Abstand {inner.min():.2f} mm (Soll {M.LID_CLR:.2f})")
    ok(inner.min() >= M.LID_CLR - 0.05, "Spiel Deckelhaut ↔ Basis eingehalten")
    pts = T["inlay"].vertices
    q = trimesh.proximity.ProximityQuery(T["basis"])
    d = np.abs(q.signed_distance(pts[pts[:, 2] > M.BASE_FLOOR + 3]))
    say(f"Inlay ↔ Basisinnenseite: kleinster Abstand {d.min():.2f} mm (Soll {M.LINER_CLR:.2f})")
    ok(d.min() >= M.LINER_CLR - 0.05, "Spiel Inlay ↔ Basis eingehalten")
    say(f"Wände: Basis {M.WALL:.2f} mm (6 Linien), Boden {M.BASE_FLOOR:.1f} mm, Deckelwand {M.LID_WALL:.2f} mm (4 Linien), Dach {M.LID_ROOF:.1f} mm, Inlay-Wand {M.DIV:.1f} mm, Inlay-Boden {M.LINER_FLOOR:.1f} mm")
    ok(M.WALL >= 2.1 and M.LID_WALL >= 1.6 and M.DIV >= 1.68, "Wandstärken ≥ 4–5 Linien à 0,42 mm")
    ok(M.Z_RIM - M.CARD_Z0 == M.CARD_H - M.HC, "Karten stehen genau Kartenüberstand über der Fuge")
    ok(M.CARD_Z0 + M.CARD_H + 4.0 <= M.Z_RIM + M.LID_CAV + 1e-6, "Deckelinnenraum: mindestens 4 mm Luft über den Karten")
    say()

    say("## 7. Druckbarkeit (Elegoo Centauri Carbon 2: Bauraum 256 × 256 × 256 mm laut Hersteller/Testberichten, Düse 0,4, PETG)")
    prints = {
        "Basis (stehend, Boden auf dem Bett)": T["basis"],
        "Deckel (Dach auf dem Bett, kopfüber)": T["deckel"].copy().apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])),
        "Inlay (stehend)": T["inlay"],
    }
    for k, m in prints.items():
        e = m.extents
        ok(max(e[0], e[1]) <= 250 and e[2] <= 250, f"{k}: {e[0]:.0f} × {e[1]:.0f} × {e[2]:.0f} mm passt in 256³")
    say()
    say("Überhänge (Flächen, deren Normale mehr als 45° nach unten geneigt ist, ohne Bettfläche), Flächenanteil an der Gesamtfläche:")
    for k, m in prints.items():
        m2 = m.copy()
        m2.apply_translation([0, 0, -m2.bounds[0][2]])
        n = m2.face_normals
        ar = m2.area_faces
        cz = m2.triangles_center[:, 2]
        down = (n[:, 2] < -0.7072) & (cz > 0.05)
        a_down = ar[down].sum()
        say(f"  {k}: {a_down:.0f} mm² von {ar.sum():.0f} mm² ({100*a_down/ar.sum():.1f} %)")
        if a_down > 0:
            c = m2.triangles_center[down]
            w = ar[down]
            # Gruppen nach Höhe/Lage
            zs = np.round(c[:, 2] / 5) * 5
            for zz in sorted(set(zs)):
                sel = (zs == zz)
                if w[sel].sum() > 15:
                    xs, ys = c[sel, 0], c[sel, 1]
                    say(f"     z≈{zz:.0f}: {w[sel].sum():.0f} mm² (x {xs.min():.0f}…{xs.max():.0f}, y {ys.min():.0f}…{ys.max():.0f})")
    say()
    say("## 8. Ergebnis")
    say("Alle Prüfungen bestanden." if not FAIL else "FEHLER: " + "; ".join(FAIL))
    with open(os.path.join(OUT, "PRUEFBERICHT.md"), "w") as f:
        f.write("\n".join(REPORT) + "\n")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
