"""Prüfung: neuer Deckel + Rasteinsatz + Klemmlasche an der gedruckten Basis v2. Schreibt out/PRUEFBERICHT.md.
Aufruf: python3 check_deckel.py"""
import math, os, sys
import numpy as np
import trimesh
import model_v2 as V
import deckel as D

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
LINES, FAILS = [], []
RHO, E = 1.27, 1800.0      # ANNAHMEN PETG
MU = 0.3                   # ANNAHME Reibung PETG/PETG


def say(s=""):
    LINES.append(s)
    print(s)


def ok(c, t):
    say(("OK    " if c else "FEHLER ") + t)
    if not c:
        FAILS.append(t)


def vol(m):
    return 0.0 if m.is_empty() else m.volume()


def inter(a, b):
    return vol(a ^ b)


def tm(m):
    me = m.to_mesh()
    return trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts), process=False)


say("# Prüfbericht: neuer Deckel für die gedruckte Basis v2 (automatisch erzeugt von deckel_fuer_v2/check_deckel.py)")
say()
say(f"Basis = Kartenbox v2 (Commit e8504ba, model_v2.py), unverändert. Deckel außen {2 * D.HX_L + 2 * V.BX:.1f} × {2 * D.HY_L + 2 * V.BY:.1f} × {V.H:.1f} mm "
    f"(vorn und seitlich {D.S_N:.2f} mm über der Basis, hinten bündig), Stülprand bis {D.Z_S:.0f} mm ({D.OV:.0f} mm über die Basis).")
base, inl, lid, ins, clip, cpin = V.base(), V.inlay(), D.lid(), D.insert(), D.clip(), D.clip_pin()
hpin = V.pin() + V.pin().mirror([1, 0, 0])
cards = V.cards_stack(V.card_mesh())
lid_asm = lid + clip + cpin
base_asm = base + ins

say()
say("## 1. Netze")
for n, m in (("Deckel", lid), ("Rasteinsatz", ins), ("Klemmlasche", clip), ("Laschenstift", cpin), ("Lasche wie gedruckt (vorgebogen)", D.clip_free()[0])):
    t = tm(m)
    ok(m.status().name == "NoError" and t.is_watertight and len(t.split(only_watertight=False)) == 1,
       f"{n}: wasserdicht, ein Körper, {vol(m) / 1000:.2f} cm³ ≈ {vol(m) / 1000 * RHO:.0f} g massiv")

say()
say("## 2. Geschlossen (Überschneidung in mm³)")
for n, a, b in (("Deckel ↔ Basis", lid, base), ("Deckel ↔ Inlay", lid, inl), ("Deckel ↔ 30 Karten", lid, cards), ("Deckel ↔ Rasteinsatz", lid, ins),
                ("Rasteinsatz ↔ Basis (Zahn frei in der Rastnut)", ins, base), ("Rasteinsatz ↔ Inlay", ins, inl),
                ("Klemmlasche ↔ Basis", clip, base), ("Klemmlasche ↔ Rasteinsatz (Haken frei darunter)", clip, ins), ("Klemmlasche ↔ Deckel", clip, lid),
                ("Laschenstift ↔ Lasche", cpin, clip), ("Scharnierstifte ↔ Deckel", hpin, lid)):
    v = inter(a, b)
    ok(v < 0.05, f"{n}: {v:.3f}")
v = inter(cpin, lid)
press = math.pi / 4 * (V.PIN_D ** 2 - V.HOLE_PRESS ** 2) * (D.CHEEK_W - 0.3)
ok(v <= press * 1.3 + 1, f"Laschenstift ↔ Deckel: {v:.1f} mm³ = gewollte Pressung im linken Lagerbock (rechnerisch {press:.1f})")

# Einbauwege
worst = max(inter(ins.translate([0, -dy, 0]), base) for dy in np.arange(0.5, 6.0, 0.5))
ok(worst < 0.05, f"Rasteinsatz lässt sich waagerecht von vorn in die Mulde schieben, Zahn voran in die Rastnut: {worst:.3f} mm³")
worst = max(inter(cpin.translate([dx, 0, 0]), lid - D.cheeks()) + inter(cpin.translate([dx, 0, 0]), clip) for dx in np.arange(1.0, 40.0, 1.0))
ok(worst < 0.05, f"Laschenstift lässt sich von rechts einschieben: {worst:.3f} mm³")

# Lage des Hakens in der Fingermulde
tip = tm(clip ^ V.box(-D.HOOK_W / 2, D.Y_BF + 0.01, D.Z_HC - 6, D.HOOK_W / 2, D.Y_BF + 5, D.Z_HC + 0.01))
_, dd, _ = trimesh.proximity.closest_point(tm(base), tip.vertices)
say(f"Haken in der Fingermulde der Basis: kleinster Abstand zur Mulde {dd.min():.2f} mm")
ok(dd.min() >= 0.2, "Haken hat in der Fingermulde Luft (≥ 0,2 mm)")

say()
say("## 3. Deckelschwenk (um die Scharnierachse der Basis, 1°-Schritte)")
hook_zone = V.box(-D.CL_X - 1, -90, D.Z_HC - 8, D.CL_X + 1, D.Y_BF + D.HOOK_D + 1.0, D.Z_INS1 + 1)
stop, max_other, hook_d = None, 0.0, []
for a in range(0, 141):
    L = V.rot_lid(lid_asm, a)
    hit = L ^ base_asm
    v_all, v_hook = vol(hit), vol(hit ^ hook_zone)
    if a <= 20 and v_hook > 0:
        b = (hit ^ hook_zone).bounding_box()
        hook_d.append(b[4] - b[1])
    if v_all - v_hook > 0.05:
        if a >= 60:
            stop = a
            break
        max_other = max(max_other, v_all - v_hook)
    if a > 0:
        max_other = max(max_other, inter(L, inl), inter(L, cards))
ok(max_other < 0.05, f"0° bis Anschlag frei: Stülprand (vorn, seitlich, schräger Auslauf hinten), Lasche, Inlay, 30 Karten (größte Überschneidung {max_other:.3f} mm³)")
ok(stop is not None and 90 <= stop <= 115, f"Anschlag wie v2 bei {stop}°: Deckel bleibt offen stehen")
lt = tm(V.rot_lid(lid_asm, stop or 96))
ok(lt.center_mass[1] > V.Y_H, f"Schwerpunkt des offenen Deckels {lt.center_mass[1] - V.Y_H:+.1f} mm hinter der Achse")
if hook_d:
    say(f"Haken beim Schließen: größte Überdeckung quer {max(hook_d):.2f} mm (= Federweg, höchstens {D.HOOK_D + D.CL_GAP:.2f} mm)")
    ok(max(hook_d) <= D.HOOK_D + D.CL_GAP + 0.3, "Haken überdeckt höchstens so weit, wie die Lasche federn soll (in 1°-Schritten gemessen)")
# Reserve am Stülprand: Basis um 0,2 mm dicker gedruckt
worst = 0.0
for a in range(1, 25):
    worst = max(worst, inter(V.rot_lid(lid - D.cheeks(), a), V.outer_body(0, V.P, extra=-0.2) - V.box(-200, 30, -1, 200, 200, 200)))
say(f"Reserve: Basis außen 0,2 mm dicker gedruckt (ohne Scharnierbereich): Überschneidung beim Aufschwenken {worst:.3f} mm³")
ok(worst < 0.05, "Stülprand schwenkt auch bei 0,2 mm Übermaß der Basis frei")

say()
say("## 4. Verschluss (rechnerisch)")
py_, pz_ = D.clip_pivot()
t, b = D.CL_T, D.CL_W
I = b * t ** 3 / 12
L_h = pz_ - (D.Z_HC - D.HOOK_FLAT / 2)
L_g = pz_ - (D.Z_GRIP + 2.9)
L_p = pz_ - (D.Z_PAD + 0.75)
_, d_pre = D.clip_free()
P0 = 3 * E * I * d_pre / L_p ** 3
dh = D.HOOK_D + 0.2
P_open = dh * 6 * E * I / (L_h ** 2 * (3 * L_g - L_h)) + P0 * L_p / L_g
eps = P_open * L_g * (t / 2) / I / E
say(f"Feder {b:.0f} × {t:.1f} mm; Wurzel → Haken {L_h:.0f} mm, → Griffnase {L_g:.0f} mm; gedruckt {d_pre:.2f} mm vorgebogen → drückt geschlossen mit ca. {P0:.1f} N unten an die Basis")
say(f"Öffnen: Haken {dh:.1f} mm unter dem Einsatz hervorziehen, an der Griffnase ca. {P_open:.1f} N; Dehnung an der Wurzel {eps * 100:.2f} % (ANNAHME E = {E:.0f} MPa)")
ok(eps < 0.015, "Dehnung < 1,5 % (Lasche auf der Seite gedruckt, Biegung entlang der Schichten)")
ok(P_open <= 9, f"Öffnen mit einem Finger hinter der Griffnase: ca. {P_open:.0f} N")
P_hook = 3 * E * I * dh / L_h ** 3 + P0 * L_p / L_h
ta = math.tan(math.radians(D.LEAD_ANG))
W_close = P_hook * (MU + ta) / (1 - MU * ta)
ok(W_close <= 15, f"Schließen: Deckel zudrücken, Haken gleitet über die Fase des Einsatzes und schnappt darunter, ca. {W_close:.0f} N")
# Vorspannung: Haken bleibt frei
back = d_pre * L_h ** 2 * (3 * L_p - L_h) / (2 * L_p ** 3)
hook_in = d_pre * L_h / L_p - back
ok(hook_in < dd.min() - 0.05, f"Vorspannung über den Druckpunkt: Haken steht {hook_in:.2f} mm weiter innen als gezeichnet, Luft in der Mulde bleibt {dd.min() - hook_in:.2f} mm")
say("Halten: Hakenoberseite und Unterkante des Einsatzes sind waagerecht – Zug am Deckel drückt den Haken nicht heraus. "
    "Der Einsatz hängt mit seinem Zahn in der alten Rastnut (30°); die schräge Fläche will ihn dabei nach vorn drücken, "
    f"daran hindert ihn der Stülprand ({D.SK_CLR} mm Luft, Zahn steckt {V.GROOVE_D - 0.2:.1f} mm in der Nut).")
ok(D.SK_CLR < V.GROOVE_D - 0.2 - 0.3, "Einsatz kann unter Zug höchstens bis zum Stülprand ausweichen und bleibt dabei in der Nut (≥ 0,3 mm Rest)")
ok(D.Z_S <= 70.0, f"Stülprand reicht bis {D.Z_S:.0f} mm, deckt den Einsatz auf Höhe der Rastnut (70–71 mm) ab")
A_hook = D.HOOK_W * (D.HOOK_FLAT + 0.5)
F_hook, F_pin = A_hook * 15.0, 2 * math.pi / 4 * V.PIN_D ** 2 * 10.0
A_tooth = 2 * D.X_INS * 1.5
F_tooth = A_tooth * 10.0
F_lip = 2 * D.X_INS * 1.5 * 10.0
say(f"Grobe Tragkraft (ANNAHMEN Scherfestigkeit 10–15 MPa): Haken {F_hook:.0f} N, Stift {F_pin:.0f} N, Zahn des Einsatzes {F_tooth:.0f} N, "
    f"Rand der Rastnut in der Basis {F_lip:.0f} N. Deckel wiegt ca. {vol(lid) / 1000 * RHO:.0f} g.")
ok(min(F_hook, F_pin, F_tooth, F_lip) >= 100, "Verschluss trägt ≥ 100 N (Tragen, Umkippen, Box auf dem Kopf mit Karten)")

say()
say("## 5. Wände")
o = tm(D.lid_outer()).sample(20000)
o = o[(o[:, 2] > D.Z_S + 1) & (o[:, 2] < V.P - 1) & (o[:, 1] < D.RUN_Y - 1) & (np.abs(o[:, 0]) > D.CHEEK_X1 + 2)]
_, d1, _ = trimesh.proximity.closest_point(tm(D.lid_inner()), o)
say(f"Stülprand: kleinste {d1.min():.2f} mm, Median {np.median(d1):.2f} mm")
ok(d1.min() >= D.SK_T - 0.15, f"Stülprand ≥ {D.SK_T - 0.15:.2f} mm")
o = tm(D.lid_outer()).sample(20000)
o = o[(o[:, 2] > D.SEAT_Z + D.S_N + 2.5) & (o[:, 2] < V.H - V.RT)]
_, d2, _ = trimesh.proximity.closest_point(tm(D.lid_inner()), o)
say(f"Deckelwand oberhalb: kleinste {d2.min():.2f} mm")
ok(d2.min() >= V.T - 0.2, f"Deckelwand ≥ {V.T - 0.2:.1f} mm")
say(f"Rasteinsatz {2 * D.X_INS:.1f} × {V.Y_RB - 0.1 - D.Y_BF:.1f} × {D.Z_INS1 - D.Z_INS0:.1f} mm (B × T × H), Seitenluft je {D.INS_CLR} mm")
gap = D.Z_S - (V.EAR_Z + 13)
say(f"Bandösen: Oberkante ca. {V.EAR_Z + 13:.0f} mm, Stülprand endet {gap:.1f} mm darüber")
ok(inter(lid, base) < 0.05, "Stülprand berührt die Ösen nicht")

say()
say("## 6. Druck (Centauri Carbon 2, 256³, PETG)")
for n, m in (("deckel", lid), ("einsatz", ins), ("lasche", D.clip_free()[0])):
    o = D.orient(n, m)
    b = o.bounding_box()
    ext = [b[3] - b[0], b[4] - b[1], b[5] - b[2]]
    ok(max(ext) <= 250, f"{n} in Druckausrichtung {ext[0]:.0f} × {ext[1]:.0f} × {ext[2]:.0f} mm")
    t = tm(o)
    n_, a_ = t.face_normals, t.area_faces
    sel = (n_[:, 2] < -math.cos(math.radians(45)) - 1e-6) & (t.triangles_center[:, 2] > 0.25)
    say(f"    Überhang > 45°: {a_[sel].sum():.0f} mm² (Tropfenbohrungen zählen mit)")

say()
say("## 7. Ergebnis")
say("Alle Prüfungen bestanden." if not FAILS else f"{len(FAILS)} NICHT bestanden:\n" + "\n".join("- " + f for f in FAILS))
open(os.path.join(OUT, "PRUEFBERICHT.md"), "w").write("\n".join(LINES) + "\n")
sys.exit(1 if FAILS else 0)
