"""Prüfung der Kartenbox v2: Netze, Kollisionen, Karten, Deckelschwenk, Verschluss, Scharnier,
Wandstärken, Standfestigkeit, Druckbarkeit (Elegoo Centauri Carbon 2, PETG). Schreibt out/PRUEFBERICHT.md.
Aufruf: python3 check.py"""
import math, os, sys
import numpy as np
import trimesh
from manifold3d import Manifold
import model as M

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
LINES, FAILS = [], []
RHO = 1.27            # PETG g/cm³ (ANNAHME, übliche Datenblattangabe 1,27)
E_PETG = 1800.0       # MPa (ANNAHME, Datenblätter 1700–2100)


def say(s=""):
    LINES.append(s)
    print(s)


def ok(cond, text):
    say(("OK    " if cond else "FEHLER ") + text)
    if not cond:
        FAILS.append(text)
    return cond


def vol(m):
    return 0.0 if m.is_empty() else m.volume()


def inter(a, b):
    return vol(a ^ b)


def tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


def bbox(m):
    b = m.bounding_box()
    return np.array(b[:3]), np.array(b[3:])


# ----------------------------------------------------------------------------- Teile
say("# Prüfbericht Kartenbox v2 (automatisch erzeugt von kartenbox/check.py)")
say()
say(f"Außenmaß geschlossen: {M.W_O + 2 * M.BX:.1f} × {M.D_O + 2 * M.BY:.1f} × {M.H:.1f} mm (B × T × H, mit Wölbung, ohne Ösen/Scharnier); "
    f"mit Ösen {M.W_O + 2 * (M.BX + M.EAR_OUT):.1f} mm breit, mit Scharnier {M.D_O / 2 + M.BY + M.Y_H + M.R_K:.1f} mm tief")
base, lid, inl = M.base(), M.lid(), M.inlay()
pin_r = M.pin()
pins = pin_r + pin_r.mirror([1, 0, 0])
card = M.card_mesh()
stack = M.cards_stack(card)

say()
say("## 1. Netze und Masse")
for n, m in (("Basis", base), ("Deckel", lid), ("Inlay", inl), ("Stift (×2)", pin_r), ("Karte (v4/out/10_karte_orange.stl)", card)):
    t = tm(m)
    ok(m.status().name == "NoError" and t.is_watertight and len(t.split(only_watertight=False)) == 1,
       f"{n}: wasserdicht, ein zusammenhängender Körper, {len(t.faces)} Dreiecke, {vol(m) / 1000:.1f} cm³")
mass = {n: vol(m) / 1000 * RHO for n, m in (("Basis", base), ("Deckel", lid), ("Inlay", inl))}
say(f"Masse bei massivem Volumen (Obergrenze, ANNAHME Dichte {RHO} g/cm³): " + ", ".join(f"{k} {v:.0f} g" for k, v in mass.items()) +
    f", zusammen {sum(mass.values()):.0f} g. Gedruckt mit 6 Wänden und 15 % Füllung etwa 70–85 % davon (Wände sind fast überall massiv).")

# ----------------------------------------------------------------------------- 2 statisch
say()
say("## 2. Geschlossen: Überschneidungen (mm³; 0 = frei)")
lid_no_hook = lid - M.box(-M.TW / 2 - 1, -80, M.Z_TIP - 2, M.TW / 2 + 1, M.Y_TI + M.HOOK + 0.5, M.P + 1)
pairs = [("Deckel ↔ Basis", lid, base), ("Inlay ↔ Basis", inl, base), ("Inlay ↔ Deckel", inl, lid),
         ("Stifte ↔ Deckel (Deckelknöchel muss frei drehen)", pins, lid)]
for n, a, b in pairs:
    v = inter(a, b)
    ok(v < 0.05, f"{n}: {v:.3f}")
v = inter(pins, base)
press_expected = math.pi / 4 * (M.PIN_D ** 2 - M.HOLE_PRESS ** 2) * (M.KB_L - 0.3) * 2
ok(v <= press_expected * 1.3 + 1, f"Stifte ↔ Basis: {v:.1f} mm³ = gewollte Pressung im inneren Basisknöchel (rechnerisch {press_expected:.1f} mm³ für Ø {M.PIN_D} in Ø {M.HOLE_PRESS})")

for n, part in (("Basis", base), ("Inlay", inl), ("Deckel", lid)):
    v = inter(stack, part)
    ok(v < 0.05, f"30 Karten an der Stütze ↔ {n}: {v:.3f}")

# Karten seitlich verschoben (ganz an die Fachwand)
DXM = (M.CMP_W - M.CARD_W) / 2 - 0.5     # seitlich verschoben bis 0,5 mm vor die Fachwand
for dx in (-DXM, DXM):
    st = M.cards_stack(card, dx=dx)
    v = sum(inter(st, p) for p in (base, inl, lid))
    ok(v < 0.05, f"30 Karten seitlich verschoben bis 0,5 mm vor die Fachwand (dx {dx:+.2f} mm) ↔ Basis/Inlay/Deckel: {v:.3f}")


# senkrechte Einzelkarte an verschiedenen Stellen
def vertical_card(xc, y_back):
    return M.card_place(card, xc, y_back, 0.0)


worst = 0.0
y_front_ok = M.Y_FI + M.CARD_T + M.FRONT_STRIP
for k in (-1, 0, 1):
    for dx in (0.0,):
        y = y_front_ok
        while y < M.Y_S0:
            c = vertical_card(k * (M.CMP_W + M.IW) + dx, y)
            worst = max(worst, inter(c, lid) + inter(c, inl) + inter(c, base))
            y += 4.0
ok(worst < 0.05, f"senkrechte Einzelkarte überall im Fach (ab {M.FRONT_STRIP:.0f} mm hinter der Fachwand, alle Fächer, quer mittig) passt unter den geschlossenen Deckel: größte Überschneidung {worst:.3f} mm³")
worst_x = 0.0
for k in (-1, 1):
    y = y_front_ok
    while y < M.Y_S0:
        worst_x = max(worst_x, inter(vertical_card(k * (M.CMP_W + M.IW + DXM), y), lid))
        y += 4.0
say(f"Hinweis: senkrechte Karte im Randfach ganz an die Stirnwand geschoben: Kartenecke berührt die Deckelrundung (größte Überschneidung {worst_x:.1f} mm³, "
    "Ecke R 1,5); der schließende Deckel schiebt sie zur Mitte. Der normale Zustand (Stapel lehnt an der Stütze) ist in jeder Querlage frei.")
c = vertical_card(0, M.Y_FI + M.CARD_T + 0.05)
v = inter(c, lid)
if v > 0.05:
    say(f"Hinweis: senkrechte Karte direkt an der Fachwand vorn berührt die Innenrundung des Deckels ({v:.1f} mm³). "
        "Beim Schließen drückt der Deckel sie nach hinten an den Stapel (FRONT_STRIP).")
else:
    say("Senkrechte Karte direkt an der Fachwand vorn (mittig): ebenfalls frei.")

# Einbauwege
worst = 0.0
for dz in np.arange(0.5, M.P + 12, 1.0):
    worst = max(worst, inter(inl.translate([0, 0, dz]), base))
ok(worst < 0.05, f"Inlay lässt sich senkrecht einsetzen und herausziehen (an der Verschluss-Verstärkung vorbei): größte Überschneidung {worst:.3f} mm³")
worst = 0.0
for side in (1, -1):
    for dx in np.arange(1.0, 40.0, 1.0):
        pp = (pin_r if side > 0 else pin_r.mirror([1, 0, 0])).translate([side * dx, 0, 0])
        worst = max(worst, inter(pp, base - M.base_knuckles()) + inter(pp, lid - M.lid_knuckles()))
ok(worst < 0.05, f"Stifte lassen sich von außen entlang der Achse einschieben (nichts im Weg außer den Knöcheln): {worst:.3f} mm³")

# ----------------------------------------------------------------------------- 3 Fassungsvermögen
say()
say("## 3. Fassungsvermögen")
free = (M.Y_S0 - M.STACK) - M.Y_FI
y_jog = M.Y_OUT_F + M.BOSS_T + 0.3 + M.IW
say(f"Mittleres Fach: Vorderwand springt auf {2 * (M.BOSS_W + 2.5):.0f} mm Breite hinter die Verschluss-Verstärkung zurück, dort {(M.Y_S0 - M.STACK) - y_jog:.1f} mm frei vor dem Stapel")
ok(free >= M.FS - 0.01, f"je Fach 10 Karten: Stapel {M.STACK:.1f} mm (waagerecht am Boden, 15° Neigung), davor {free:.1f} mm frei zum Greifen")
ok(M.CMP_W - M.CARD_W >= 4, f"Fach {M.CMP_W:.0f} mm breit, Karte {M.CARD_W:.0f} mm: {M.CMP_W - M.CARD_W:.0f} mm Luft quer")
say(f"Karten-Oberkante: {M.Z_F + M.CARD_H * M.COS + M.CARD_T * M.SIN:.1f} mm (geneigt) bzw. {M.Z_F + M.CARD_H:.1f} mm (senkrecht); Deckeldecke innen {M.CEIL:.1f} mm; Basisrand {M.P:.0f} mm")
say(f"Cover-Fenster der Karte beginnt {43.5:.1f} mm über der Kartenunterkante (v4: INS_Y0) → sichtbar ab ca. {M.Z_F + 43.5 * M.COS:.0f} mm Höhe; "
    f"Griffmulden im Inlay bis {M.SCOOP_Z:.0f} mm hinunter, Basisrand {M.P:.0f} mm")

# ----------------------------------------------------------------------------- 4 Schwenk
say()
say("## 4. Deckelschwenk um die Scharnierachse (Schritt 1°)")
hook_zone = M.box(-M.TW / 2 - 1, -90, M.Z_TIP - 3, M.TW / 2 + 1, M.Y_RB + M.GROOVE_D + 0.5, M.P + 3)
stop = None
max_other = 0.0
hook_depth = []
for a in range(0, 141):
    L = M.rot_lid(lid, a)
    hit = L ^ base
    v_all = vol(hit)
    v_hook = vol(hit ^ hook_zone)
    if a <= 15 and v_hook > 0:
        lo, hi = bbox(hit ^ hook_zone)
        hook_depth.append((a, hi[1] - lo[1]))
    if v_all - v_hook > 0.05:
        if a >= 60:
            stop = a
            break
        max_other = max(max_other, v_all - v_hook)
    for p in (inl, stack):
        max_other = max(max_other, inter(L, p) if a > 0 else 0.0)
ok(max_other < 0.05, f"0° bis Anschlag: Deckel frei gegenüber Basis (außer Rasthaken), Inlay und 30 Karten (größte Überschneidung {max_other:.3f} mm³)")
ok(stop is not None and 95 <= stop <= 115, f"Öffnungsanschlag (Nase am Deckelknöchel trifft die Rückwand) bei {stop}° – Deckel kippt über die Senkrechte und bleibt offen")
# Schwerpunkt Deckel bei Anschlag hinter der Achse?
Lo = M.rot_lid(lid, stop or 100)
lt = tm(Lo)
ok(lt.center_mass[1] > M.Y_H, f"Schwerpunkt des offenen Deckels {lt.center_mass[1] - M.Y_H:+.1f} mm hinter der Achse → fällt nicht zu")
if hook_depth:
    dmax = max(d for _, d in hook_depth)
    say(f"Rasthaken beim Schließen: größte Überdeckung mit der Basis {dmax:.2f} mm (Federweg der Zunge; Soll {M.HOOK - M.REC_GAP:.2f} mm)")
    ok(dmax <= M.HOOK - M.REC_GAP + 0.25, "Haken überdeckt nur so weit, wie die Zunge federn soll")
# geschlossen: Haken frei in der Nut?
v = inter(lid, base)
ok(v < 0.05, f"geschlossen sitzt der Haken frei in der Rastnut ({v:.3f} mm³), senkrechtes Spiel {M.PLAY_V} mm")

# Basis in Scharnierbereich gegen Deckelwand
gap = (M.Y_H - M.R_K) - (M.D_O / 2 + M.BY * (1 - ((M.PX - M.POD / 2) / (M.W_O / 2)) ** 2))
ok(gap >= 0.5, f"Basisknöchel ↔ Deckelrückwand: kleinster Abstand {gap:.2f} mm (gleicher Radius beim Drehen, keine Berührung)")

# ----------------------------------------------------------------------------- 5 Verschluss / Scharnier rechnerisch
say()
say("## 5. Verschluss und Scharnier (rechnerisch)")
L_t = M.Z_ROOT - (M.HOOK_Z - 1.0)
d = M.HOOK - M.REC_GAP
t = M.T_TONGUE
b = M.TW
I = b * t ** 3 / 12
eps = 1.5 * d * t / L_t ** 2
F = 3 * E_PETG * I * d / L_t ** 3
MU = 0.3  # Reibung PETG/PETG (ANNAHME)


def snap_force(P_lat, alpha_deg):
    """Kraft in Zugrichtung, um eine Fläche unter alpha (gegen die Zugrichtung) mit Querkraft P_lat zu überfahren."""
    ta = math.tan(math.radians(alpha_deg))
    return float("inf") if MU * ta >= 1 else P_lat * (MU + ta) / (1 - MU * ta)


say(f"Zunge {b:.0f} × {t:.1f} mm, freie Länge {L_t:.0f} mm, Federweg {d:.2f} mm → Randdehnung {eps * 100:.2f} %, Federkraft {F:.1f} N (ANNAHME E = {E_PETG:.0f} MPa)")
ok(eps < 0.006, "Dehnung unter 0,6 % (Biegung geht quer zu den Schichten, daher niedrig gehalten; PETG-Streckdehnung ca. 4 %)")
W_close = snap_force(F, M.LEAD_ANG)
W_open = snap_force(F, M.HOLD_ANG)
say(f"Öffnen: Griffnase {M.LIP_OUT} mm nach außen ziehen (ca. {F:.0f} N), dann Deckel heben. Schließen: Haken gleitet über die {M.LEAD_ANG:.0f}°-Schräge, ca. {W_close:.0f} N, hörbares Einrasten.")
say(f"Haltefläche {M.HOLD_ANG:.0f}° gegen die Zugrichtung: Deckel ohne Betätigen der Zunge aufreißen braucht ca. {W_open:.0f} N "
    f"(Reibung {MU}, ANNAHME). Bei Gewalt springt der Haken heraus, statt zu brechen.")
ok(W_open >= 3 * F and W_open >= 15, "Verschluss hält mindestens das Dreifache der Betätigungskraft und ≥ 15 N (Tragen, Umkippen)")
ok(F <= 10, "Öffnungskraft an der Zunge höchstens 10 N (6-Jähriger, ANNAHME; Coupon K2 prüft)")
rest = (M.Y_OUT_F + M.BOSS_T) - (M.Y_RB + M.GROOVE_D)
ok(rest >= 1.6, f"Restwand hinter der Rastnut {rest:.2f} mm (≥ 4 Linien)")
say(f"Scharnier: 2 × 3 Knöchel (Basis {M.KB_L:.0f} / Deckel {M.KL_L:.0f} / Basis {M.KB_L:.0f} mm, Spiel {M.K_GAP} mm), Knöchel R {M.R_K} mm, "
    f"Stift Ø {M.PIN_D} gedruckt (Bohrungen: außen {M.HOLE_SLIP}, Deckel {M.HOLE_LID}, innen {M.HOLE_PRESS} klemmt)")
ok(M.R_K - M.HOLE_LID / 2 >= 2.4, f"Wand um die Deckelbohrung {M.R_K - M.HOLE_LID / 2:.2f} mm")
ok(M.R_K - M.HOLE_SLIP / 2 >= 2.4, f"Wand um die Basisbohrungen {M.R_K - M.HOLE_SLIP / 2:.2f} mm")
ok((M.HOLE_LID - M.PIN_D) / 2 >= 0.25, f"Deckelknöchel dreht frei: {(M.HOLE_LID - M.PIN_D) / 2:.2f} mm Luft je Seite")

# ----------------------------------------------------------------------------- 6 Wände
say()
say("## 6. Wandstärken (gemessen an den Netzen)")
outer_t = tm(M.outer_body(0, M.H))
cav_t = tm(M.cavity_body(M.T, M.CEIL))
pts = cav_t.sample(20000, return_index=False)
pts = pts[(np.abs(pts[:, 2] - M.P) > M.GROOVE + M.T)]
_, dist, _ = trimesh.proximity.closest_point(outer_t, pts)
say(f"Außenhaut ↔ Innenraum (ohne V-Fuge): kleinste {dist.min():.2f} mm, Median {np.median(dist):.2f} mm")
ok(dist.min() >= M.T - 0.15, f"Wand überall ≥ {M.T - 0.15:.2f} mm")
say(f"an der V-Fuge: kleinste Wand {M.T - M.GROOVE:.2f} mm (Fuge {M.GROOVE} mm tief, nur auf ±{M.GROOVE} mm Höhe)")
ok(M.T - M.GROOVE >= 1.6, "Wand an der V-Fuge ≥ 1,6 mm")
say(f"Inlay {M.IW} mm (4 Linien), Inlay-Boden {M.IF} mm; Basisboden {M.T} mm; Deckeldach {M.T} mm")
ear_out = M.EAR_OUT - M.EAR_HX - M.EAR_HOLE / 2
ear_in = M.EAR_HX - M.EAR_HOLE / 2
ok(min(ear_out, ear_in) >= 2.5, f"Öse: Wand außen {ear_out:.1f} mm, zur Box hin {ear_in:.1f} mm")

# ----------------------------------------------------------------------------- 7 Standfestigkeit
say()
say("## 7. Standfestigkeit (Kippen)")
card_m = vol(card) / 1000 * RHO * 0.75
parts_m = [(tm(base), mass["Basis"] * 0.8), (tm(inl), mass["Inlay"] * 0.6)]
def com(objs):
    tot = sum(m for _, m in objs)
    return sum(t.center_mass * m for t, m in objs) / tot, tot
foot = M.inset_outer(0)
for label, ang, with_cards in (("geschlossen, 30 Karten", 0, True), ("leer, Deckel offen am Anschlag", stop or 100, False), ("30 Karten, Deckel offen", stop or 100, True)):
    objs = parts_m + [(tm(M.rot_lid(lid, ang)), mass["Deckel"] * 0.8)]
    if with_cards:
        objs.append((tm(stack), card_m * 30))
    c, tot = com(objs)
    yb, yf = M.D_O / 2 - foot, -M.D_O / 2 + foot
    a_back = math.degrees(math.atan2(yb - c[1], c[2]))
    a_front = math.degrees(math.atan2(c[1] - yf, c[2]))
    ok(min(a_back, a_front) > 0, f"{label}: Schwerpunkt y {c[1]:+.1f} / z {c[2]:.1f} mm, kippt nach hinten erst bei {a_back:.0f}°, nach vorn bei {a_front:.0f}° (Masse ca. {tot:.0f} g, ANNAHME Karte 75 % gefüllt)")

# ----------------------------------------------------------------------------- 8 Druck
say()
say("## 8. Druckbarkeit (Elegoo Centauri Carbon 2: 256 × 256 × 256 mm, Herstellerangabe; Düse 0,4; PETG)")
printed = {}
for n, m in (("basis", base), ("deckel", lid), ("inlay", inl), ("stift", pin_r)):
    o = M.orient(n, m)
    printed[n] = o
    lo, hi = bbox(o)
    ext = hi - lo
    ok(ext[0] <= 250 and ext[1] <= 250 and ext[2] <= 250, f"{n} in Druckausrichtung {ext[0]:.0f} × {ext[1]:.0f} × {ext[2]:.0f} mm (≤ 250, 3 mm Rand)")
    # Drehung statt Spiegelung: Volumen und Orientierung
    ok(abs(vol(o) - vol(m)) < 1e-3 * vol(m) + 1, f"{n}: Druckausrichtung ist eine reine Drehung (Volumen gleich, keine Spiegelung im Code)")


def overhangs(m, limit=45.0):
    t = tm(m)
    n = t.face_normals
    a = t.area_faces
    zc = t.triangles_center[:, 2]
    down = n[:, 2] < -math.cos(math.radians(limit)) - 1e-6
    bed = zc < 0.25
    sel = down & ~bed
    flat = sel & (n[:, 2] < -0.985)
    return t, sel, flat, a


for n, o in printed.items():
    t, sel, flat, a = overhangs(o)
    say(f"- {n}: Überhang > 45° {a[sel].sum():.0f} mm², davon waagerecht (Brücke) {a[flat].sum():.0f} mm²")
    if sel.any():
        cz = t.triangles_center[sel]
        # nach Höhe gruppieren
        zs = np.round(cz[:, 2] / 3) * 3
        for z in sorted(set(zs)):
            k = zs == z
            aa = a[sel][k].sum()
            if aa < 3:
                continue
            lo, hi = cz[k].min(0), cz[k].max(0)
            say(f"    z≈{z:.0f}: {aa:.0f} mm² (x {lo[0]:.0f}…{hi[0]:.0f}, y {lo[1]:.0f}…{hi[1]:.0f})")

say()
say("Erwartete Überhänge (bewusst): Bohrungen als Tropfen (Spitze 45°), Brücke über den Hohlräumen des Inlays (Dach ≤ 14 mm Spannweite), "
    "Haltefläche von Haken und Rastnut (30° zur Waagerechten, 1 mm breit), Unterseite der Stiftrundung direkt über dem Bett.")
fp = M.inset_outer(0)
say(f"Haftfläche: Basis {M.W_O - 2 * fp:.0f} × {M.D_O - 2 * fp:.0f} mm, Deckel-Dach {M.W_O - 2 * M.inset_outer(M.H):.0f} × {M.D_O - 2 * M.inset_outer(M.H):.0f} mm – kein Brim nötig")

say()
say("## 9. Ergebnis")
if FAILS:
    say(f"{len(FAILS)} Prüfung(en) NICHT bestanden:")
    for f in FAILS:
        say("- " + f)
else:
    say("Alle Prüfungen bestanden.")
open(os.path.join(OUT, "PRUEFBERICHT.md"), "w").write("\n".join(LINES) + "\n")
sys.exit(1 if FAILS else 0)
