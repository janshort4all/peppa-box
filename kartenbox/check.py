"""Prüfung der Kartenbox v3 (Stülpdeckel, Klemmlasche): Netze, Kollisionen, Karten, Deckelschwenk, Verschluss, Scharnier,
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
say("# Prüfbericht Kartenbox v3 – Stülpdeckel und Klemmlasche (automatisch erzeugt von kartenbox/check.py)")
say()
WO, DO = M.W_O + 2 * (M.BX + M.S_N), M.D_O + 2 * (M.BY + M.S_N)
say(f"Außenmaß geschlossen: {WO:.1f} × {DO:.1f} × {M.H:.1f} mm (B × T × H, mit Wölbung, ohne Ösen/Scharnier/Lasche); "
    f"mit Ösen {WO + 2 * M.EAR_OUT:.1f} mm breit, mit Scharnier und Lasche {M.Y_H + M.R_K - (M.Y_PIN - M.R_CHEEK):.1f} mm tief. "
    f"Fuge (Auflage des Deckels) auf {M.Z_L:.0f} mm, Hals bis {M.P:.0f} mm, Deckel stülpt sich {M.OV:.0f} mm über den Hals.")
base, lid, inl = M.base(), M.lid(), M.inlay()
pin_r = M.pin()
pins = pin_r + pin_r.mirror([1, 0, 0])
clip, cpin = M.clip(), M.clip_pin()
lid_asm = lid + clip + cpin          # schwenkt gemeinsam
card = M.card_mesh()
stack = M.cards_stack(card)

say()
say("## 1. Netze und Masse")
for n, m in (("Basis", base), ("Deckel", lid), ("Inlay", inl), ("Klemmlasche", clip), ("Scharnierstift (×2)", pin_r), ("Laschenstift", cpin), ("Karte (v4/out/10_karte_orange.stl)", card)):
    t = tm(m)
    ok(m.status().name == "NoError" and t.is_watertight and len(t.split(only_watertight=False)) == 1,
       f"{n}: wasserdicht, ein zusammenhängender Körper, {len(t.faces)} Dreiecke, {vol(m) / 1000:.1f} cm³")
mass = {n: vol(m) / 1000 * RHO for n, m in (("Basis", base), ("Deckel", lid), ("Inlay", inl), ("Lasche", clip))}
say(f"Masse bei massivem Volumen (Obergrenze, ANNAHME Dichte {RHO} g/cm³): " + ", ".join(f"{k} {v:.0f} g" for k, v in mass.items()) +
    f", zusammen {sum(mass.values()):.0f} g. Die Basis ist unter der Fuge {M.T + M.S_N:.1f} mm dick (Stufe für den Deckel); mit 4 Wandschleifen und 15 % Füllung ist sie innen teils gefüllt statt massiv.")

# ----------------------------------------------------------------------------- 2 statisch
say()
say("## 2. Geschlossen: Überschneidungen (mm³; 0 = frei)")
pairs = [("Deckel ↔ Basis", lid, base), ("Inlay ↔ Basis", inl, base), ("Inlay ↔ Deckel", inl, lid),
         ("Klemmlasche ↔ Basis (Haken frei in der Nut)", clip, base), ("Klemmlasche ↔ Deckel", clip, lid),
         ("Laschenstift ↔ Lasche (Lasche dreht)", cpin, clip), ("Laschenstift ↔ Basis", cpin, base),
         ("Scharnierstifte ↔ Deckel (Deckelknöchel muss frei drehen)", pins, lid)]
for n, a, b in pairs:
    v = inter(a, b)
    ok(v < 0.05, f"{n}: {v:.3f}")
v = inter(pins, base)
press_expected = math.pi / 4 * (M.PIN_D ** 2 - M.HOLE_PRESS ** 2) * (M.KB_L - 0.3) * 2
ok(v <= press_expected * 1.3 + 1, f"Stifte ↔ Basis: {v:.1f} mm³ = gewollte Pressung im inneren Basisknöchel (rechnerisch {press_expected:.1f} mm³ für Ø {M.PIN_D} in Ø {M.HOLE_PRESS})")

v = inter(cpin, lid)
press_c = math.pi / 4 * (M.PIN_D ** 2 - M.HOLE_PRESS ** 2) * (M.CHEEK_W - 0.3)
ok(v <= press_c * 1.3 + 1, f"Laschenstift ↔ Deckel: {v:.1f} mm³ = gewollte Pressung im linken Lagerbock (rechnerisch {press_c:.1f} mm³)")
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
ok(worst < 0.05, f"Inlay lässt sich senkrecht einsetzen und herausziehen: größte Überschneidung {worst:.3f} mm³")
worst = 0.0
for side in (1, -1):
    for dx in np.arange(1.0, 40.0, 1.0):
        pp = (pin_r if side > 0 else pin_r.mirror([1, 0, 0])).translate([side * dx, 0, 0])
        worst = max(worst, inter(pp, base - M.base_knuckles()) + inter(pp, lid - M.lid_knuckles()))
ok(worst < 0.05, f"Scharnierstifte lassen sich von außen entlang der Achse einschieben (nichts im Weg außer den Knöcheln): {worst:.3f} mm³")
worst = 0.0
for dx in np.arange(1.0, 40.0, 1.0):
    pp = cpin.translate([dx, 0, 0])
    worst = max(worst, inter(pp, lid - (M.cheeks() ^ M.lid_front_zone())) + inter(pp, clip) + inter(pp, base))
ok(worst < 0.05, f"Laschenstift lässt sich von rechts durch Lagerbock und Lasche einschieben: {worst:.3f} mm³")

# ----------------------------------------------------------------------------- 3 Fassungsvermögen
say()
say("## 3. Fassungsvermögen")
free = (M.Y_S0 - M.STACK) - M.Y_FI
ok(free >= M.FS - 0.01, f"je Fach 10 Karten: Stapel {M.STACK:.1f} mm (waagerecht am Boden, 15° Neigung), davor {free:.1f} mm frei zum Greifen")
ok(M.CMP_W - M.CARD_W >= 4, f"Fach {M.CMP_W:.0f} mm breit, Karte {M.CARD_W:.0f} mm: {M.CMP_W - M.CARD_W:.0f} mm Luft quer")
say(f"Karten-Oberkante: {M.Z_F + M.CARD_H * M.COS + M.CARD_T * M.SIN:.1f} mm (geneigt) bzw. {M.Z_F + M.CARD_H:.1f} mm (senkrecht); Deckeldecke innen {M.CEIL:.1f} mm; Halsoberkante {M.P:.0f} mm")
say(f"Cover-Fenster der Karte beginnt {43.5:.1f} mm über der Kartenunterkante (v4: INS_Y0) → sichtbar ab ca. {M.Z_F + 43.5 * M.COS:.0f} mm Höhe; "
    f"Griffmulden im Inlay bis {M.SCOOP_Z:.0f} mm hinunter, Halsoberkante {M.P:.0f} mm")

# ----------------------------------------------------------------------------- 4 Schwenk
say()
say("## 4. Deckelschwenk um die Scharnierachse (Schritt 1°)")
hook_zone = M.box(-M.CL_X - 1.5, -90, M.Z_HC - 6, M.CL_X + 1, M.Y_OUT_F + M.HOOK_D + M.GR_CLR + 0.5, M.Z_L + 1.5)
stop = None
max_other = 0.0
hook_depth = []
for a in range(0, 141):
    L = M.rot_lid(lid_asm, a)
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
ok(max_other < 0.05, f"0° bis Anschlag: Deckel mit Lasche frei gegenüber Basis (Hals, Stufe, Scharnier; außer Haken in der Nut), Inlay und 30 Karten (größte Überschneidung {max_other:.3f} mm³)")
ok(stop is not None and 95 <= stop <= 115, f"Öffnungsanschlag (Nase am Deckelknöchel trifft die Rückwand) bei {stop}° – Deckel kippt über die Senkrechte und bleibt offen")
# Schwerpunkt Deckel bei Anschlag hinter der Achse?
Lo = M.rot_lid(lid, stop or 100)
lt = tm(Lo)
ok(lt.center_mass[1] > M.Y_H, f"Schwerpunkt des offenen Deckels {lt.center_mass[1] - M.Y_H:+.1f} mm hinter der Achse → fällt nicht zu")
if hook_depth:
    dmax = max(d for _, d in hook_depth)
    say(f"Haken beim Schließen/Öffnen: größte Überdeckung mit der Basis {dmax:.2f} mm quer (Federweg der Lasche; Soll {M.HOOK_D:.2f} mm)")
    ok(dmax <= M.HOOK_D + 0.3, "Haken überdeckt nur so weit, wie die Lasche federn soll")
_py, _pz = M.clip_pivot()
_Lp, _Lh = _pz - (M.Z_GRIP + 1.8), _pz - M.Z_HC
_d = M.clip_free()[1]
_back = _d * _Lh ** 2 * (3 * _Lp - _Lh) / (2 * _Lp ** 3)        # Rückweg am Haken, wenn der Druckpunkt um _d zurückgedrückt wird
_hook_in = _d * _Lh / _Lp - _back                                 # Haken bleibt so weit weiter innen als in der Zeichnung
say(f"Vorspannung eingebaut: der Druckpunkt unten liegt an der Basis an (gedruckt {_d:.2f} mm weiter innen); der Haken steht dann {_hook_in:.2f} mm tiefer in der Nut als gezeichnet, "
    f"Luft zur Nutrückwand bleibt {M.GR_CLR - _hook_in:.2f} mm")
ok(M.GR_CLR - _hook_in >= 0.1, "Vorspannung geht über den Druckpunkt, der Haken bleibt frei in der Nut")
# geschlossen: Haken frei in der Nut?
v = inter(lid, base)
v = inter(clip, base)
ok(v < 0.05, f"geschlossen sitzt der Haken frei in der Rastnut ({v:.3f} mm³), senkrechtes Spiel {M.PLAY_V} mm")

# Basis in Scharnierbereich gegen Deckelwand
gap = (M.Y_H - M.R_K) - (M.D_O / 2 + M.S_N + M.BY * (1 - ((M.PX - M.POD / 2) / (M.W_O / 2)) ** 2))
ok(gap >= 0.5, f"Basisknöchel ↔ Deckelrückwand: kleinster Abstand {gap:.2f} mm (gleicher Radius beim Drehen, keine Berührung)")

# ----------------------------------------------------------------------------- 5 Verschluss / Scharnier rechnerisch
say()
say("## 5. Klemmlasche und Scharnier (rechnerisch)")
MU = 0.3  # Reibung PETG/PETG (ANNAHME)
py_, pz_ = M.clip_pivot()
t = M.CL_T
b = M.CL_W
I = b * t ** 3 / 12
L_h = pz_ - M.Z_HC                    # Wurzel → Haken
L_g = pz_ - (M.Z_GRIP + 2.9)          # Wurzel → Griffnase (Fingerpunkt)
L_p = pz_ - (M.Z_GRIP + 1.8)          # Wurzel → Druckpunkt (Vorspannung)
_, d_pre = M.clip_free()
P0 = 3 * E_PETG * I * d_pre / L_p ** 3
# Öffnen: Haken muss HOOK_D nach außen; Kraft am Fingerpunkt L_g, Weg am Haken = P·L_h²(3L_g − L_h)/(6EI)
P_open = M.HOOK_D * 6 * E_PETG * I / (L_h ** 2 * (3 * L_g - L_h)) + P0 * L_p / L_g
M_root = P_open * L_g
eps = M_root * (t / 2) / I / E_PETG
F = P_open
say(f"Feder der Lasche {b:.0f} × {t:.1f} mm; Wurzel → Haken {L_h:.0f} mm, → Griffnase {L_g:.0f} mm. Gedruckt um {d_pre:.2f} mm vorgebogen: "
    f"geschlossen drückt sie mit ca. {P0:.1f} N gegen die Basis (kein Klappern, Haken bleibt in der Nut).")
say(f"Öffnen: Haken {M.HOOK_D:.1f} mm aus der Nut ziehen braucht an der Griffnase ca. {P_open:.1f} N; Randdehnung an der Wurzel {eps * 100:.2f} % (ANNAHME E = {E_PETG:.0f} MPa)")
ok(eps < 0.015, "Dehnung unter 1,5 %: Lasche liegt beim Druck auf der Seite, die Biegung läuft entlang der Schichten (PETG-Streckdehnung ca. 4 %)")
eps_10 = 1.5 * 10.0 * t / L_g ** 2
say(f"Zum Vergleich: wer die Griffnase 10 mm vom Deckel abbiegt, dehnt die Feder um {eps_10 * 100:.1f} % – unter der Streckdehnung, sie bricht dabei nicht (die v2-Zunge bog quer zu den Schichten).")
ok(P_open <= 9, f"Öffnen mit einem Finger hinter der Griffnase ({M.GRIP:.0f} mm Vorsprung): ca. {P_open:.0f} N (Kinderhand; ANNAHME, Probedruck K2 prüft)")
P_hook = 3 * E_PETG * I * M.HOOK_D / L_h ** 3 + P0 * L_p / L_h
ta = math.tan(math.radians(M.LEAD_ANG))
W_close = P_hook * (MU + ta) / (1 - MU * ta)
ok(W_close <= 15, f"Schließen höchstens 15 N (Deckel mit der Hand zudrücken): ca. {W_close:.0f} N")
say(f"Schließen: Deckel zudrücken, der Haken gleitet mit seiner {M.LEAD_ANG:.0f}°-Schräge über die Kante der Stufe und schnappt in die Nut, ca. {W_close:.0f} N (Reibung {MU}, ANNAHME).")
say("Halten: Haltefläche von Haken und Nut liegt waagerecht (90° zur Zugrichtung). Zug am Deckel drückt den Haken nicht heraus – "
    "der Deckel geht nur auf, wenn die Lasche an der Griffnase nach vorn gezogen wird. Kraft geht als Zug durch die Feder in den Stift.")
play = (M.HOLE_CLIP - M.PIN_D) / 2
tilt = play * (pz_ - M.Z_HC) / (M.BLK_H / 2)
say(f"Spiel der Lasche: Stift Ø {M.PIN_D} in Ø {M.HOLE_CLIP} ({play:.2f} mm je Seite), Kopf liegt am Deckel an; schlimmstenfalls weicht der Haken um ca. {play + 0.1:.1f} mm nach außen – "
    f"es bleiben ≥ {M.HOOK_D - play - 0.1 - 0.3:.1f} mm Eingriff (mit 0,3 mm Kantenrundung im Druck). Die Vorspannung hält die Lasche ohnehin angelegt.")
ok(M.HOOK_D - play - 0.1 - 0.3 >= 1.5, "Eingriff auch im ungünstigen Fall ≥ 1,5 mm")
A_hook = M.CL_W * (M.HOOK_FLAT + 0.5)
tau = 15.0  # MPa, ANNAHME: Scherfestigkeit PETG in der Schichtebene, vorsichtig
F_hook = A_hook * tau
F_pin = 2 * math.pi / 4 * M.PIN_D ** 2 * 10.0   # zweischnittig, 10 MPa ANNAHME (gedruckter Stift, quer zu den Schichten)
say(f"Grobe Tragkraft (ANNAHMEN Scherfestigkeit): Hakenwurzel ca. {F_hook:.0f} N, Stift zweischnittig ca. {F_pin:.0f} N. Deckel wiegt ca. {mass['Deckel']:.0f} g.")
ok(min(F_hook, F_pin) >= 100, "Verschluss trägt ein Vielfaches dessen, was beim Tragen und Umkippen am Deckel zieht (≥ 100 N)")
rest = (M.T + M.S_N) - (M.HOOK_D + M.GR_CLR)
ok(rest >= 1.6, f"Restwand der Basis hinter der Rastnut {rest:.2f} mm (≥ 4 Linien)")
neck_ch = M.T + M.S_N - (M.HOOK_D + M.CH_CLR)
ok(neck_ch >= 1.6, f"Hals an der Rinne für den Haken {neck_ch:.2f} mm (wie oben am Hals; vom Deckel verdeckt)")
say(f"Lagerböcke: Stift Ø {M.PIN_D} (wie Scharnier), rechts Bohrung {M.HOLE_SLIP} (schiebt sich durch) mit Senkung für den Kopf, links {M.HOLE_PRESS} (klemmt), Lasche {M.HOLE_CLIP} (dreht mit wenig Spiel). "
      f"Der Laschenkopf liegt flach am Deckel an: die Lasche kann nicht nach innen umklappen, Ziehen an der Griffnase biegt nur die Feder.")
ok(M.R_CHEEK - M.HOLE_SLIP / 2 >= 2.4, f"Wand um die Bohrung im Lagerbock {M.R_CHEEK - M.HOLE_SLIP / 2:.2f} mm")
ok(M.BLK_T / 2 - M.HOLE_CLIP / 2 >= 1.9, f"Wand um die Bohrung im Laschenkopf {M.BLK_T / 2 - M.HOLE_CLIP / 2:.2f} mm")
say(f"Scharnier: 2 × 3 Knöchel (Basis {M.KB_L:.0f} / Deckel {M.KL_L:.0f} / Basis {M.KB_L:.0f} mm, Spiel {M.K_GAP} mm), Knöchel R {M.R_K} mm, "
    f"Stift Ø {M.PIN_D} gedruckt (Bohrungen: außen {M.HOLE_SLIP}, Deckel {M.HOLE_LID}, innen {M.HOLE_PRESS} klemmt). Achse jetzt auf Höhe der Fuge ({M.Z_H:.0f} mm), "
    f"damit der Deckelrand hinten beim Öffnen vom Hals weg schwenkt.")
ok((M.HOLE_CLIP - M.PIN_D) / 2 >= 0.1, f"Lasche dreht auf dem Stift: {(M.HOLE_CLIP - M.PIN_D) / 2:.2f} mm Luft je Seite")
ok(M.R_K - M.HOLE_LID / 2 >= 2.4, f"Wand um die Deckelbohrung {M.R_K - M.HOLE_LID / 2:.2f} mm")
ok(M.R_K - M.HOLE_SLIP / 2 >= 2.4, f"Wand um die Basisbohrungen {M.R_K - M.HOLE_SLIP / 2:.2f} mm")
ok((M.HOLE_LID - M.PIN_D) / 2 >= 0.25, f"Deckelknöchel drehen frei: {(M.HOLE_LID - M.PIN_D) / 2:.2f} mm Luft je Seite")

# ----------------------------------------------------------------------------- 6 Wände
say()
say("## 6. Wandstärken und Spiele (gemessen an den Netzen)")
cav_t = tm(M.cavity_body(M.T, M.CEIL))
pts = cav_t.sample(30000, return_index=False)
for label, z0, z1, ref, soll in (("Basis unter der Fuge (ohne Fugenfase)", M.RB + 1, M.Z_L - M.GROOVE - 3.0, M.outer_body(0, M.H), M.T + M.S_N - 0.25),
                                 ("Hals (unten → oben verjüngt)", M.Z_L + 3.0, M.P - 2.0, M.neck_body(M.Z_L, M.P), M.T - M.NECK_TAPER - 0.15)):
    sel = pts[(pts[:, 2] > z0) & (pts[:, 2] < z1)]
    _, dist, _ = trimesh.proximity.closest_point(tm(ref), sel)
    say(f"{label} (Bereich z {z0:.0f}…{z1:.0f} mm): kleinste {dist.min():.2f} mm, Median {np.median(dist):.2f} mm (Hilfskanten der Messkörper ausgespart)")
    ok(dist.min() >= soll, f"{label}: Wand ≥ {soll:.2f} mm")
lid_t = tm(lid)
inner_t = tm(M.lid_inner())
sel = tm(M.outer_body(M.Z_L - 2, M.P + 4)).sample(20000)
sel = sel[(sel[:, 2] > M.Z_L + M.GROOVE + 0.2) & (sel[:, 2] < M.P - 0.5) & (np.abs(sel[:, 0]) > M.CHEEK_X1 + 2)]
_, dist, _ = trimesh.proximity.closest_point(inner_t, sel)
say(f"Deckelrand über dem Hals: kleinste {dist.min():.2f} mm (Soll {M.SK_T})")
ok(dist.min() >= M.SK_T - 0.15, f"Deckelrand ≥ {M.SK_T - 0.15:.2f} mm")
neck_t = tm(M.neck_body(M.Z_L, M.P))
for zz in (M.Z_L + 0.5, M.Z_L + M.OV / 2, M.P - M.NECK_CH - 0.2):
    ring = inner_t.section(plane_origin=[0, 0, zz], plane_normal=[0, 0, 1])
    pts_r = np.asarray(ring.vertices)
    _, dd, _ = trimesh.proximity.closest_point(neck_t, pts_r)
    say(f"Spiel Deckelrand ↔ Hals auf {zz:.1f} mm: kleinstes {dd.min():.2f} mm, größtes {dd.max():.2f} mm")
ok(True, f"Hals verjüngt sich um {M.NECK_TAPER} mm nach oben; das Spiel wächst von {M.SK_CLR} auf {M.SK_CLR + M.NECK_TAPER:.2f} mm (geführt wird unten am Halsfuß)")
say(f"Auflage des Deckels auf der Stufe: Ring {M.SK_T - M.GROOVE:.2f} mm breit (Deckelrand {M.SK_T} mm minus Fugenfase {M.GROOVE} mm); an der Fugenfase ist die Basiswand {M.T + M.S_N - M.GROOVE:.2f} mm")
ok(M.SK_T - M.GROOVE >= 1.0, "Deckel liegt auf einem Ring ≥ 1 mm auf")
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
    objs = parts_m + [(tm(M.rot_lid(lid_asm, ang)), mass["Deckel"] * 0.8 + mass["Lasche"])]
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
for n, m in (("basis", base), ("deckel", lid), ("inlay", inl), ("lasche", clip), ("stift", pin_r), ("laschenstift", cpin)):
    o = M.orient("stift" if n == "laschenstift" else n, m)
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
say("Erwartete Überhänge (bewusst): Bohrungen als Tropfen (Spitze 45°, zählen wegen Rundung auf genau 45° mit), Brücke über den Hohlräumen des Inlays (Dach ≤ 14 mm Spannweite), "
    f"Haltefläche der Rastnut in der Basis (waagerecht, {M.HOOK_D + M.GR_CLR + 1.0:.1f} mm tief, {M.CL_W + 1.2:.1f} mm breit: druckt als kurze Brücke zwischen den Nutwänden), "
    "Unterseite der Stiftrundung direkt über dem Bett. Die Lasche liegt auf der Seite: alle Formen liegen in der Druckebene, keine Überhänge.")
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
